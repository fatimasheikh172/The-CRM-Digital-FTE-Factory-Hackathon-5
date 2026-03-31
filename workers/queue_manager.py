"""
TechCorp Customer Success AI Agent - Queue Manager

In-memory message queue that simulates Kafka behavior.
Will be replaced by real Kafka in Exercise 2.5.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict


# ============================================================================
# KAFKA TOPIC SIMULATION
# ============================================================================

class KafkaTopics:
    """Kafka topic names for the Customer Success Agent."""
    
    TICKETS_INCOMING = "fte.tickets.incoming"
    EMAIL_INBOUND = "fte.channels.email.inbound"
    WHATSAPP_INBOUND = "fte.channels.whatsapp.inbound"
    WEBFORM_INBOUND = "fte.channels.webform.inbound"
    ESCALATIONS = "fte.escalations"
    METRICS = "fte.metrics"
    DLQ = "fte.dlq"  # Dead Letter Queue
    
    # All topics
    ALL_TOPICS = {
        TICKETS_INCOMING,
        EMAIL_INBOUND,
        WHATSAPP_INBOUND,
        WEBFORM_INBOUND,
        ESCALATIONS,
        METRICS,
        DLQ,
    }


# ============================================================================
# MESSAGE QUEUE
# ============================================================================

class MessageQueue:
    """
    In-memory message queue that simulates Kafka behavior.
    
    This class uses Python asyncio Queue to simulate Kafka topics.
    Messages are also persisted to JSON files for durability.
    
    Usage:
        queue = MessageQueue()
        queue.publish(KafkaTopics.TICKETS_INCOMING, {"message": "test"})
        await queue.consume(KafkaTopics.TICKETS_INCOMING, handler_func)
    """
    
    def __init__(self, simulation_dir: str = None):
        """
        Initialize the message queue.
        
        Args:
            simulation_dir: Directory for persisting messages.
        """
        # In-memory queues per topic
        self._queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        
        # Message storage for persistence
        self._messages: Dict[str, List[Dict]] = defaultdict(list)
        
        # Set simulation directory
        if simulation_dir is None:
            self.simulation_dir = Path(__file__).parent.parent / "simulation"
        else:
            self.simulation_dir = Path(simulation_dir)
        
        # Ensure simulation directory exists
        self.simulation_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing messages from file
        self._load_messages()
    
    def _get_queue_file(self, topic: str) -> Path:
        """Get the file path for a topic's messages."""
        # Sanitize topic name for filename
        safe_name = topic.replace(".", "_")
        return self.simulation_dir / f"queue_{safe_name}.json"
    
    def _load_messages(self) -> None:
        """Load messages from simulation files."""
        for topic in KafkaTopics.ALL_TOPICS:
            file_path = self._get_queue_file(topic)
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                        self._messages[topic] = messages
                        # Add to queue
                        for msg in messages:
                            if msg.get('status') == 'pending':
                                self._queues[topic].put_nowait(msg)
                except (json.JSONDecodeError, FileNotFoundError):
                    self._messages[topic] = []
    
    def _save_messages(self, topic: str) -> None:
        """Save messages for a topic to file."""
        file_path = self._get_queue_file(topic)
        messages = self._messages.get(topic, [])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, default=str)
    
    def publish(self, topic: str, message: Dict[str, Any]) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic name (use KafkaTopics constants).
            message: Message dictionary.
        
        Returns:
            Message ID.
        """
        # Add metadata
        message_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        message['message_id'] = message_id
        message['topic'] = topic
        message['timestamp'] = datetime.now().isoformat()
        message['status'] = 'pending'
        
        # Store message
        self._messages[topic].append(message)
        
        # Add to queue
        self._queues[topic].put_nowait(message)
        
        # Save to file
        self._save_messages(topic)
        
        return message_id
    
    async def consume(self, topic: str, handler: Callable, timeout: float = 5.0) -> None:
        """
        Consume messages from a topic.
        
        Args:
            topic: Topic name.
            handler: Async function to call for each message.
            timeout: Timeout for waiting for messages.
        """
        queue = self._queues[topic]
        
        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            
            # Call handler
            try:
                await handler(message)
                message['status'] = 'processed'
            except Exception as e:
                message['status'] = 'error'
                message['error'] = str(e)
            
            # Save updated status
            self._save_messages(topic)
            
        except asyncio.TimeoutError:
            pass  # No message available
    
    def get_queue_size(self, topic: str) -> int:
        """
        Get the number of pending messages in a topic.
        
        Args:
            topic: Topic name.
        
        Returns:
            Number of pending messages.
        """
        return self._queues[topic].qsize()
    
    def clear_queue(self, topic: str) -> int:
        """
        Clear all messages from a topic.
        
        Args:
            topic: Topic name.
        
        Returns:
            Number of messages cleared.
        """
        count = 0
        queue = self._queues[topic]
        
        while not queue.empty():
            try:
                queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        
        # Clear stored messages
        self._messages[topic] = []
        self._save_messages(topic)
        
        return count
    
    def get_messages(self, topic: str, status: str = None) -> List[Dict]:
        """
        Get messages from a topic.
        
        Args:
            topic: Topic name.
            status: Optional status filter.
        
        Returns:
            List of messages.
        """
        messages = self._messages.get(topic, [])
        
        if status:
            messages = [m for m in messages if m.get('status') == status]
        
        return messages
    
    def get_all_topics_status(self) -> Dict[str, Dict]:
        """
        Get status of all topics.
        
        Returns:
            Dictionary with topic stats.
        """
        status = {}
        
        for topic in KafkaTopics.ALL_TOPICS:
            messages = self._messages.get(topic, [])
            pending = sum(1 for m in messages if m.get('status') == 'pending')
            processed = sum(1 for m in messages if m.get('status') == 'processed')
            error = sum(1 for m in messages if m.get('status') == 'error')
            
            status[topic] = {
                "total": len(messages),
                "pending": pending,
                "processed": processed,
                "error": error,
                "queue_size": self._queues[topic].qsize()
            }
        
        return status


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_queue(simulation_dir: str = None) -> MessageQueue:
    """
    Create a message queue instance.
    
    Args:
        simulation_dir: Optional simulation directory.
    
    Returns:
        MessageQueue instance.
    """
    return MessageQueue(simulation_dir=simulation_dir)


# ============================================================================
# MAIN (for testing)
# ============================================================================

async def main():
    """Test the message queue."""
    print("=" * 60)
    print("Message Queue Test")
    print("=" * 60)
    
    queue = MessageQueue()
    
    # Test publish
    print("\n1. Publishing messages...")
    msg_id = queue.publish(KafkaTopics.TICKETS_INCOMING, {
        "customer_id": "test@example.com",
        "message": "Test message",
        "channel": "email"
    })
    print(f"   Published: {msg_id}")
    
    # Test queue size
    print(f"\n2. Queue size: {queue.get_queue_size(KafkaTopics.TICKETS_INCOMING)}")
    
    # Test consume
    print("\n3. Consuming message...")
    received = []
    
    async def handler(msg):
        received.append(msg)
        print(f"   Received: {msg['message']}")
    
    await queue.consume(KafkaTopics.TICKETS_INCOMING, handler, timeout=1.0)
    
    # Test status
    print("\n4. Topic status:")
    status = queue.get_all_topics_status()
    for topic, stats in status.items():
        if stats['total'] > 0:
            print(f"   {topic}: {stats}")
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
