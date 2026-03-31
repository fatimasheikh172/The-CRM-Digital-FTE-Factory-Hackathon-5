"""
TechCorp Customer Success AI Agent - Kafka Client

Real Apache Kafka producer and consumer implementation
using aiokafka for async operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from kafka.admin import KafkaAdminClient as SyncKafkaAdminClient

from production.config import AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# KAFKA TOPICS
# ============================================================================

TOPICS = {
    "tickets_incoming": "fte.tickets.incoming",
    "email_inbound": "fte.channels.email.inbound",
    "whatsapp_inbound": "fte.channels.whatsapp.inbound",
    "webform_inbound": "fte.channels.webform.inbound",
    "escalations": "fte.escalations",
    "metrics": "fte.metrics",
    "dlq": "fte.dlq"
}


# ============================================================================
# KAFKA PRODUCER
# ============================================================================

class FTEKafkaProducer:
    """
    Sends messages to Kafka topics.
    
    Usage:
        producer = FTEKafkaProducer()
        await producer.start()
        await producer.publish("fte.tickets.incoming", {"message": "test"})
        await producer.stop()
    """

    def __init__(self, bootstrap_servers: str = None):
        """
        Initialize the Kafka producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (default: localhost:9092)
        """
        self.bootstrap_servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS
        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False

    async def start(self) -> None:
        """
        Initialize AIOKafkaProducer.
        
        Sets up producer with:
        - bootstrap_servers = localhost:9092
        - value_serializer = JSON encode
        """
        if self._running:
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                request_timeout_ms=30000
            )
            await self._producer.start()
            self._running = True
            logger.info(f"Kafka producer started on {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self) -> None:
        """Stop producer cleanly."""
        if not self._running:
            return

        try:
            if self._producer:
                await self._producer.stop()
            self._running = False
            logger.info("Kafka producer stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}")
        finally:
            self._producer = None

    async def publish(self, topic: str, event: dict) -> bool:
        """
        Publish a single event to a Kafka topic.
        
        Args:
            topic: Topic name to publish to.
            event: Event dictionary to publish.
            
        Returns:
            True if success, False if failed.
        """
        if not self._running or not self._producer:
            logger.warning(f"Producer not running, cannot publish to {topic}")
            return False

        try:
            # Add timestamp to event
            event['kafka_timestamp'] = datetime.now().isoformat()
            
            # Send to Kafka topic
            future = await self._producer.send_and_wait(
                topic,
                value=event,
                key=topic
            )
            
            logger.debug(f"Published to {topic}: partition={future.partition}, offset={future.offset}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False

    async def publish_batch(
        self, topic: str, events: list
    ) -> int:
        """
        Send multiple events at once.
        
        Args:
            topic: Topic name to publish to.
            events: List of event dictionaries.
            
        Returns:
            Count of successful sends.
        """
        if not self._running or not self._producer:
            logger.warning(f"Producer not running, cannot publish batch to {topic}")
            return 0

        success_count = 0
        
        for event in events:
            try:
                # Add timestamp to event
                event['kafka_timestamp'] = datetime.now().isoformat()
                
                await self._producer.send_and_wait(
                    topic,
                    value=event,
                    key=topic
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to publish batch event to {topic}: {e}")
                
        logger.info(f"Published {success_count}/{len(events)} events to {topic}")
        return success_count

    @property
    def is_running(self) -> bool:
        """Check if producer is running."""
        return self._running


# ============================================================================
# KAFKA CONSUMER
# ============================================================================

class FTEKafkaConsumer:
    """
    Receives messages from Kafka topics.
    
    Usage:
        consumer = FTEKafkaConsumer(["fte.tickets.incoming"], "processor-group")
        await consumer.start()
        await consumer.consume(handler_func)
        await consumer.stop()
    """

    def __init__(self, topics: list, group_id: str, bootstrap_servers: str = None):
        """
        Initialize the Kafka consumer.
        
        Args:
            topics: List of topics to subscribe to.
            group_id: Consumer group ID.
            bootstrap_servers: Kafka bootstrap servers.
        """
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """
        Initialize AIOKafkaConsumer.
        
        Sets up consumer with:
        - bootstrap_servers = localhost:9092
        - group_id = provided group_id
        - value_deserializer = JSON decode
        - auto_offset_reset = "earliest"
        """
        if self._running:
            return

        try:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else {},
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )
            await self._consumer.start()
            self._running = True
            logger.info(f"Kafka consumer started for topics {self.topics}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop(self) -> None:
        """Stop consumer cleanly."""
        if not self._running:
            return

        try:
            self._running = False
            if self._consumer:
                await self._consumer.stop()
            logger.info("Kafka consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka consumer: {e}")
        finally:
            self._consumer = None

    async def consume(self, handler: Callable) -> None:
        """
        Listen for messages continuously.
        
        Args:
            handler: Async function to call for each message.
                     Signature: handler(topic, message)
        """
        if not self._running or not self._consumer:
            logger.warning("Consumer not running, cannot consume")
            return

        try:
            async for msg in self._consumer:
                try:
                    topic = msg.topic
                    message = msg.value
                    
                    # Call handler for each message
                    if asyncio.iscoroutinefunction(handler):
                        await handler(topic, message)
                    else:
                        handler(topic, message)
                        
                except Exception as e:
                    logger.error(f"Error processing message from {msg.topic}: {e}")
                    # Continue consuming - don't stop on error
                    
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
        except Exception as e:
            logger.error(f"Consumer error: {e}")

    @property
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running


# ============================================================================
# KAFKA HEALTH CHECK
# ============================================================================

class KafkaHealthCheck:
    """
    Health check utilities for Kafka connection.
    
    Usage:
        connected = await KafkaHealthCheck.check_connection()
        topics = await KafkaHealthCheck.list_topics()
        exists = await KafkaHealthCheck.check_topic_exists("fte.tickets.incoming")
    """

    @staticmethod
    async def check_connection(bootstrap_servers: str = None) -> bool:
        """
        Try to connect to Kafka.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers.
            
        Returns:
            True if connected, False if failed.
        """
        servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS
        
        producer = None
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=servers,
                request_timeout_ms=30000
            )
            await producer.start()
            
            # Try to send a test message (metadata request)
            await producer.send_and_wait("__health_check__", value=b"test", key=b"test")
            
            await producer.stop()
            logger.info(f"Kafka connection check successful: {servers}")
            return True
            
        except Exception as e:
            logger.warning(f"Kafka connection check failed: {e}")
            if producer:
                try:
                    await producer.stop()
                except:
                    pass
            return False

    @staticmethod
    async def list_topics(bootstrap_servers: str = None) -> list:
        """
        Return list of existing topics.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers.
            
        Returns:
            List of topic names.
        """
        servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS
        
        try:
            # Use sync admin client for listing topics
            admin_client = SyncKafkaAdminClient(
                bootstrap_servers=servers,
                request_timeout_ms=5000
            )
            topics = list(admin_client.list_topics())
            admin_client.close()
            return topics
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return []

    @staticmethod
    async def check_topic_exists(topic: str, bootstrap_servers: str = None) -> bool:
        """
        Check if a topic exists.
        
        Args:
            topic: Topic name to check.
            bootstrap_servers: Kafka bootstrap servers.
            
        Returns:
            True if topic exists, False otherwise.
        """
        try:
            topics = await KafkaHealthCheck.list_topics(bootstrap_servers)
            return topic in topics
        except Exception:
            return False


# ============================================================================
# KAFKA TOPIC ADMIN
# ============================================================================

class KafkaTopicAdmin:
    """
    Admin utilities for creating and managing Kafka topics.
    
    Usage:
        admin = KafkaTopicAdmin()
        await admin.create_topic("fte.tickets.incoming", partitions=3)
        await admin.create_topics_if_not_exist(topic_configs)
    """

    def __init__(self, bootstrap_servers: str = None):
        """
        Initialize the Kafka topic admin.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers.
        """
        self.bootstrap_servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS

    async def create_topic(
        self,
        topic: str,
        partitions: int = 1,
        replication_factor: int = 1
    ) -> dict:
        """
        Create a single Kafka topic.
        
        Args:
            topic: Topic name.
            partitions: Number of partitions.
            replication_factor: Replication factor.
            
        Returns:
            Dict with status: {"topic": name, "created": bool, "existed": bool}
        """
        try:
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                request_timeout_ms=10000
            )
            await admin_client.start()
            
            # Check if topic exists
            existing_topics = await self._list_topics_async(admin_client)
            
            if topic in existing_topics:
                await admin_client.close()
                return {"topic": topic, "created": False, "existed": True}
            
            # Create topic
            new_topic = NewTopic(
                name=topic,
                num_partitions=partitions,
                replication_factor=replication_factor
            )
            
            await admin_client.create_topics([new_topic])
            await admin_client.close()
            
            logger.info(f"Created topic: {topic} (partitions={partitions})")
            return {"topic": topic, "created": True, "existed": False}
            
        except Exception as e:
            logger.error(f"Failed to create topic {topic}: {e}")
            return {"topic": topic, "created": False, "existed": False, "error": str(e)}
        finally:
            try:
                await admin_client.close()
            except:
                pass

    async def _list_topics_async(self, admin_client: AIOKafkaAdminClient) -> list:
        """List topics using async admin client."""
        try:
            metadata = await admin_client._client.cluster.fetch_all_metadata()
            return list(metadata.topics.keys())
        except:
            # Fallback to sync client
            return KafkaHealthCheck.list_topics(self.bootstrap_servers)

    async def create_topics_if_not_exist(
        self,
        topic_configs: Dict[str, Dict[str, int]]
    ) -> Dict[str, dict]:
        """
        Create multiple topics if they don't exist.
        
        Args:
            topic_configs: Dict of {topic_name: {partitions, replication_factor}}
            
        Returns:
            Dict of results for each topic.
        """
        results = {}
        
        for topic, config in topic_configs.items():
            result = await self.create_topic(
                topic,
                partitions=config.get("partitions", 1),
                replication_factor=config.get("replication_factor", 1)
            )
            results[topic] = result
            
        return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def create_producer() -> FTEKafkaProducer:
    """Create and start a Kafka producer."""
    producer = FTEKafkaProducer()
    await producer.start()
    return producer


async def create_consumer(topics: list, group_id: str) -> FTEKafkaConsumer:
    """Create and start a Kafka consumer."""
    consumer = FTEKafkaConsumer(topics, group_id)
    await consumer.start()
    return consumer


# ============================================================================
# MAIN (for testing)
# ============================================================================

async def main():
    """Test the Kafka client."""
    print("=" * 60)
    print("Kafka Client Test")
    print("=" * 60)

    # Test connection
    print("\n1. Testing connection...")
    connected = await KafkaHealthCheck.check_connection()
    print(f"   Connected: {connected}")

    if not connected:
        print("   Kafka not available, skipping further tests")
        return

    # Test list topics
    print("\n2. Listing topics...")
    topics = await KafkaHealthCheck.list_topics()
    print(f"   Topics: {topics}")

    # Test producer
    print("\n3. Testing producer...")
    producer = FTEKafkaProducer()
    await producer.start()
    
    success = await producer.publish("fte.tickets.incoming", {
        "test": "message",
        "timestamp": datetime.now().isoformat()
    })
    print(f"   Published: {success}")
    
    await producer.stop()

    # Test consumer (brief)
    print("\n4. Testing consumer...")
    consumer = FTEKafkaConsumer(["fte.tickets.incoming"], "test-group")
    await consumer.start()
    
    received = []
    
    async def handler(topic, msg):
        received.append(msg)
        print(f"   Received from {topic}: {msg}")
    
    # Consume for 2 seconds
    consume_task = asyncio.create_task(consumer.consume(handler))
    await asyncio.sleep(2)
    await consumer.stop()
    consume_task.cancel()
    
    try:
        await consume_task
    except asyncio.CancelledError:
        pass

    print(f"   Messages received: {len(received)}")

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
