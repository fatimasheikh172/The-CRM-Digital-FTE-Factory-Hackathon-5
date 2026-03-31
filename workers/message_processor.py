"""
TechCorp Customer Success AI Agent - Unified Message Processor

Processes incoming messages from ALL channels through the Gemini agent.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import asyncpg

from production.config import AgentConfig
from production.agent.customer_success_agent import CustomerSuccessAgent
from production.agent.formatters import format_response
from workers.queue_manager import MessageQueue, KafkaTopics
from workers.metrics_collector import MetricsCollector
from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from channels.web_form_handler import WebFormHandler
from kafka_client import FTEKafkaProducer, FTEKafkaConsumer, KafkaHealthCheck, TOPICS


# ============================================================================
# UNIFIED MESSAGE PROCESSOR
# ============================================================================

class UnifiedMessageProcessor:
    """
    Processes incoming messages from ALL channels through the Gemini agent.
    
    This is the main worker that:
    1. Receives messages from the queue
    2. Resolves customer identity
    3. Gets/creates conversation
    4. Stores incoming message
    5. Runs Gemini agent
    6. Stores agent response
    7. Collects metrics
    
    Usage:
        processor = UnifiedMessageProcessor()
        await processor.start()
    """
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize the message processor.

        Args:
            mock_mode: If True, use mock agent (no API key needed).
        """
        self.mock_mode = mock_mode
        self.queue = MessageQueue()
        self.agent = CustomerSuccessAgent(mock_mode=mock_mode)
        self.metrics = MetricsCollector()

        # Channel handlers
        self.gmail = GmailHandler(simulation_mode=True)
        self.whatsapp = WhatsAppHandler(simulation_mode=True)
        self.web_form = WebFormHandler()

        # Kafka producer and consumer (initialized in start())
        self._kafka_producer: Optional[FTEKafkaProducer] = None
        self._kafka_consumer: Optional[FTEKafkaConsumer] = None
        
        # Mode flag
        self._use_kafka = False

        # Running flag
        self._running = False
    
    async def process_message(self, topic: str, message: Dict) -> Dict:
        """
        Process a single message through the full pipeline.
        
        Args:
            topic: Topic the message came from.
            message: Message dictionary.
        
        Returns:
            Processing result dictionary.
        """
        start_time = time.time()
        result = {
            "topic": topic,
            "message_id": message.get("message_id"),
            "status": "success",
            "error": None,
            "channel": None,
            "customer_id": None,
            "conversation_id": None,
            "escalated": False,
            "latency_ms": 0
        }
        
        try:
            # Step 1: Log incoming message
            channel = message.get("channel", "unknown")
            result["channel"] = channel
            print(f"  [1/8] Processing {channel} message...")
            
            # Step 2: Validate message
            if not self._validate_message(message):
                raise ValueError("Invalid message: missing required fields")
            
            # Step 3: Resolve customer
            customer_id = await self.resolve_customer(message)
            result["customer_id"] = customer_id
            print(f"  [2/8] Customer resolved: {customer_id}")
            
            # Step 4: Get or create conversation
            content = message.get("content") or message.get("message", "")
            conversation_id = await self.get_or_create_conversation(
                customer_id, channel, content
            )
            result["conversation_id"] = conversation_id
            print(f"  [3/8] Conversation: {conversation_id}")
            
            # Step 5: Store incoming message
            metadata = message.get("metadata", {})
            await self.store_incoming_message(
                conversation_id, channel, content, metadata
            )
            print(f"  [4/8] Incoming message stored")
            
            # Step 6: Load conversation history
            history = await self.load_conversation_history(conversation_id)
            print(f"  [5/8] Loaded {len(history)} history messages")
            
            # Step 7: Run Gemini agent
            customer_email = message.get("customer_email", "")
            customer_phone = message.get("customer_phone", "")
            
            agent_result = await self.agent.run(
                message=content,
                channel=channel,
                customer_id=customer_id,
                customer_email=customer_email,
                customer_phone=customer_phone,
                conversation_history=history
            )
            
            result["escalated"] = agent_result.get("escalated", False)
            output = agent_result.get("output", "")
            tool_calls = agent_result.get("tool_calls", [])
            print(f"  [6/8] Agent response generated (escalated: {result['escalated']})")
            
            # Step 8: Store agent response
            await self.store_agent_response(
                conversation_id, channel, output,
                agent_result.get("processing_time_ms", 0),
                tool_calls
            )
            print(f"  [7/8] Agent response stored")
            
            # Step 9: Collect metrics
            await self.metrics.record_message_processed(
                channel=channel,
                latency_ms=agent_result.get("processing_time_ms", 0),
                escalated=result["escalated"],
                tool_calls_count=len(tool_calls)
            )
            print(f"  [8/8] Metrics recorded")
            
            # Calculate total latency
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            # Handle error
            result["status"] = "error"
            result["error"] = str(e)
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            
            # Send apology and save to DLQ
            await self.handle_processing_error(message, e)
        
        return result
    
    def _validate_message(self, message: Dict) -> bool:
        """Validate message has required fields."""
        required = ["channel", "content"]
        for field in required:
            if field not in message and field not in message.get("metadata", {}):
                # Check alternative field names
                if field == "content" and "message" not in message:
                    return False
        return True
    
    async def resolve_customer(self, message: Dict) -> str:
        """
        Find or create customer from message.
        
        Args:
            message: Message dictionary.
        
        Returns:
            Customer ID (UUID).
        """
        customer_email = message.get("customer_email")
        customer_phone = message.get("customer_phone")
        channel = message.get("channel", "unknown")
        
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            # Try to find existing customer
            customer = None
            
            if customer_email:
                customer = await conn.fetchrow(
                    "SELECT id FROM customers WHERE email = $1",
                    customer_email
                )
            
            if not customer and customer_phone:
                customer = await conn.fetchrow(
                    "SELECT id FROM customers WHERE phone = $1",
                    customer_phone
                )
            
            if customer:
                return str(customer["id"])
            
            # Create new customer
            if customer_email:
                row = await conn.fetchrow(
                    """
                    INSERT INTO customers (email, metadata)
                    VALUES ($1, $2)
                    RETURNING id
                    """,
                    customer_email,
                    json.dumps({"first_channel": channel})
                )
            elif customer_phone:
                row = await conn.fetchrow(
                    """
                    INSERT INTO customers (phone, metadata)
                    VALUES ($1, $2)
                    RETURNING id
                    """,
                    customer_phone,
                    json.dumps({"first_channel": channel})
                )
            else:
                # Generate anonymous customer
                import uuid
                return str(uuid.uuid4())
            
            return str(row["id"])
            
        except asyncpg.PostgresError:
            # Return mock customer ID if DB unavailable
            import uuid
            return str(uuid.uuid4())
        finally:
            if conn:
                await conn.close()
    
    async def get_or_create_conversation(
        self, customer_id: str, channel: str, message: str
    ) -> str:
        """
        Get active conversation or create new one.
        
        Args:
            customer_id: Customer UUID.
            channel: Channel type.
            message: Initial message.
        
        Returns:
            Conversation ID (UUID).
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            # Check for active conversation (within last 24 hours)
            row = await conn.fetchrow(
                """
                SELECT id FROM conversations
                WHERE customer_id = $1
                  AND status = 'active'
                  AND started_at > NOW() - INTERVAL '24 hours'
                ORDER BY started_at DESC
                LIMIT 1
                """,
                customer_id
            )
            
            if row:
                return str(row["id"])
            
            # Create new conversation
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (customer_id, initial_channel, current_channel, metadata)
                VALUES ($1, $2, $2, $3)
                RETURNING id
                """,
                customer_id,
                channel,
                json.dumps({"source": "processor"})
            )
            
            return str(row["id"])
            
        except asyncpg.PostgresError:
            # Return mock conversation ID if DB unavailable
            import uuid
            return str(uuid.uuid4())
        finally:
            if conn:
                await conn.close()
    
    async def store_incoming_message(
        self, conversation_id: str, channel: str, content: str, metadata: Dict
    ) -> str:
        """
        Save customer message to database.
        
        Args:
            conversation_id: Conversation UUID.
            channel: Channel type.
            content: Message content.
            metadata: Additional metadata.
        
        Returns:
            Message ID (UUID).
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            row = await conn.fetchrow(
                """
                INSERT INTO messages (
                    conversation_id, channel, direction, role, content, metadata
                )
                VALUES ($1, $2, 'inbound', 'customer', $3, $4)
                RETURNING id
                """,
                conversation_id,
                channel,
                content,
                json.dumps(metadata) if metadata else '{}'
            )
            
            return str(row["id"]) if row else "mock_msg_id"
            
        except asyncpg.PostgresError:
            return "mock_msg_id"
        finally:
            if conn:
                await conn.close()
    
    async def store_agent_response(
        self, conversation_id: str, channel: str, content: str,
        latency_ms: int, tool_calls: List
    ) -> str:
        """
        Save agent response to database.
        
        Args:
            conversation_id: Conversation UUID.
            channel: Channel type.
            content: Response content.
            latency_ms: Processing latency.
            tool_calls: List of tool calls made.
        
        Returns:
            Message ID (UUID).
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            row = await conn.fetchrow(
                """
                INSERT INTO messages (
                    conversation_id, channel, direction, role, content,
                    latency_ms, tool_calls, metadata
                )
                VALUES ($1, $2, 'outbound', 'agent', $3, $4, $5, $6)
                RETURNING id
                """,
                conversation_id,
                channel,
                content,
                latency_ms,
                json.dumps(tool_calls) if tool_calls else '[]',
                json.dumps({"source": "gemini_agent"})
            )
            
            return str(row["id"]) if row else "mock_response_id"
            
        except asyncpg.PostgresError:
            return "mock_response_id"
        finally:
            if conn:
                await conn.close()
    
    async def load_conversation_history(self, conversation_id: str) -> List:
        """
        Load last 10 messages from conversation.
        
        Args:
            conversation_id: Conversation UUID.
        
        Returns:
            List of message dictionaries with role and content.
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            rows = await conn.fetch(
                """
                SELECT role, content, channel, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT 10
                """,
                conversation_id
            )
            
            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "channel": row["channel"]
                }
                for row in rows
            ]
            
        except asyncpg.PostgresError:
            return []
        finally:
            if conn:
                await conn.close()
    
    async def handle_processing_error(self, message: Dict, error: Exception) -> None:
        """
        Handle processing error - send apology and save to DLQ.
        
        Args:
            message: Original message.
            error: Exception that occurred.
        """
        channel = message.get("channel", "email")
        customer_email = message.get("customer_email", "")
        customer_phone = message.get("customer_phone", "")
        
        # Generate apology response
        apology = self._generate_apology(channel)
        
        # Save to DLQ
        dlq_message = {
            "original_message": message,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.now().isoformat()
        }
        self.queue.publish(KafkaTopics.DLQ, dlq_message)
        
        # Log error
        print(f"  ERROR: {error}")
        print(f"  Message saved to DLQ")
    
    def _generate_apology(self, channel: str) -> str:
        """Generate apology response for channel."""
        base = (
            "We apologize, but we encountered an issue processing your request. "
            "Your ticket has been escalated to our technical team for assistance."
        )
        return format_response(base, channel)
    
    async def start(self) -> None:
        """
        Start the processor - listen on incoming topic.
        
        Tries to connect to Kafka first. If Kafka is available, uses real
        Kafka producer/consumer. If Kafka is unavailable, falls back to
        in-memory queue.
        """
        self._running = True
        print("Starting message processor...")
        print(f"  Listening on: {KafkaTopics.TICKETS_INCOMING}")
        print(f"  Mock mode: {self.mock_mode}")
        
        # Try to connect to Kafka
        kafka_available = await KafkaHealthCheck.check_connection()
        
        if kafka_available:
            # Use real Kafka
            self._use_kafka = True
            self._kafka_producer = FTEKafkaProducer()
            self._kafka_consumer = FTEKafkaConsumer(
                [KafkaTopics.TICKETS_INCOMING],
                group_id="fte-message-processor"
            )
            
            await self._kafka_producer.start()
            await self._kafka_consumer.start()
            
            print("  Mode: REAL KAFKA")
            
            # Start consuming from Kafka
            await self._kafka_consumer.consume(self._kafka_handler)
        else:
            # Fallback to in-memory queue
            self._use_kafka = False
            print("  Mode: IN-MEMORY QUEUE (Kafka unavailable)")
            print("  WARNING: Running in fallback mode")
            
            while self._running:
                # Process messages from in-memory queue
                await self.queue.consume(
                    KafkaTopics.TICKETS_INCOMING,
                    self._queue_handler,
                    timeout=1.0
                )

    async def _kafka_handler(self, topic: str, message: Dict) -> None:
        """Handle message from Kafka."""
        print(f"  Received from Kafka topic: {topic}")
        await self.process_message(topic, message)

    async def _queue_handler(self, message: Dict) -> None:
        """Handle message from queue."""
        topic = message.get("topic", KafkaTopics.TICKETS_INCOMING)
        await self.process_message(topic, message)

    def stop(self) -> None:
        """Stop the processor."""
        self._running = False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def process_single_message(
    message: Dict,
    mock_mode: bool = True
) -> Dict:
    """
    Process a single message (convenience function).
    
    Args:
        message: Message dictionary.
        mock_mode: Use mock agent.
    
    Returns:
        Processing result.
    """
    processor = UnifiedMessageProcessor(mock_mode=mock_mode)
    topic = message.get("topic", KafkaTopics.TICKETS_INCOMING)
    return await processor.process_message(topic, message)


# ============================================================================
# MAIN (for testing)
# ============================================================================

async def main():
    """Test the message processor."""
    print("=" * 60)
    print("Unified Message Processor Test")
    print("=" * 60)
    
    processor = UnifiedMessageProcessor(mock_mode=True)
    
    # Test message
    test_message = {
        "channel": "email",
        "customer_email": "test@example.com",
        "content": "I can't login to my account",
        "metadata": {"subject": "Login Issue"}
    }
    
    print("\nProcessing test message...")
    result = await processor.process_message(
        KafkaTopics.TICKETS_INCOMING,
        test_message
    )
    
    print(f"\nResult:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
