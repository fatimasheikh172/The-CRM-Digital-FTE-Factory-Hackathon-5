"""
TechCorp Customer Success AI Agent - Kafka Tests

Tests for Kafka integration including:
- Connection tests
- Producer tests
- Consumer tests
- Topic tests
- Fallback tests
- Integration tests
"""

import asyncio
import pytest
import time
from datetime import datetime
from typing import List, Dict, Any

# Import with timeout handling
from kafka_client import (
    FTEKafkaProducer,
    FTEKafkaConsumer,
    KafkaHealthCheck,
    TOPICS,
)
from workers.queue_manager import MessageQueue, KafkaTopics


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def kafka_available():
    """Check if Kafka is available for tests."""
    return await KafkaHealthCheck.check_connection()


# ============================================================================
# TEST 1: CONNECTION TEST
# ============================================================================

class TestKafkaConnection:
    """Test Kafka connection and health checks."""

    @pytest.mark.asyncio
    async def test_kafka_connection(self, kafka_available):
        """Test that Kafka connection can be established."""
        # Kafka should be available
        assert kafka_available is True, "Kafka should be running on localhost:9092"

    @pytest.mark.asyncio
    async def test_list_topics(self, kafka_available):
        """Test listing Kafka topics."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        topics = await KafkaHealthCheck.list_topics()
        
        # Should have at least some topics
        assert len(topics) > 0, "Should have at least one topic"
        assert isinstance(topics, list), "Topics should be a list"

    @pytest.mark.asyncio
    async def test_required_topics_exist(self, kafka_available):
        """Test that all required FTE topics exist after setup."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        required_topics = list(TOPICS.values())
        
        for topic in required_topics:
            exists = await KafkaHealthCheck.check_topic_exists(topic)
            assert exists is True, f"Topic {topic} should exist"


# ============================================================================
# TEST 2: PRODUCER TEST
# ============================================================================

class TestKafkaProducer:
    """Test Kafka producer functionality."""

    @pytest.mark.asyncio
    async def test_producer_start_stop(self, kafka_available):
        """Test producer can start and stop cleanly."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        producer = FTEKafkaProducer()
        
        # Start should not raise
        await producer.start()
        assert producer.is_running is True
        
        # Stop should not raise
        await producer.stop()
        assert producer.is_running is False

    @pytest.mark.asyncio
    async def test_publish_single_message(self, kafka_available):
        """Test publishing a single message to Kafka."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        test_topic = "fte.metrics"
        test_message = {
            "test_id": "test_001",
            "content": "Test message",
            "timestamp": datetime.now().isoformat()
        }
        
        producer = FTEKafkaProducer()
        try:
            await producer.start()
            
            # Publish message
            success = await producer.publish(test_topic, test_message)
            
            assert success is True, "Publish should succeed"
        finally:
            await producer.stop()

    @pytest.mark.asyncio
    async def test_publish_batch_messages(self, kafka_available):
        """Test publishing multiple messages at once."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        test_topic = "fte.metrics"
        test_messages = [
            {"batch_id": i, "content": f"Message {i}"}
            for i in range(5)
        ]
        
        producer = FTEKafkaProducer()
        try:
            await producer.start()
            
            # Publish batch
            success_count = await producer.publish_batch(test_topic, test_messages)
            
            assert success_count == 5, f"All 5 messages should be published, got {success_count}"
        finally:
            await producer.stop()

    @pytest.mark.asyncio
    async def test_publish_with_timestamp(self, kafka_available):
        """Test that publish adds timestamp to message."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        test_topic = "fte.metrics"
        test_message = {"content": "Test with timestamp"}
        
        producer = FTEKafkaProducer()
        try:
            await producer.start()
            await producer.publish(test_topic, test_message)
        finally:
            await producer.stop()
        
        # Message should have kafka_timestamp added
        assert "kafka_timestamp" in test_message


# ============================================================================
# TEST 3: CONSUMER TEST
# ============================================================================

class TestKafkaConsumer:
    """Test Kafka consumer functionality."""

    @pytest.mark.asyncio
    async def test_consumer_start_stop(self, kafka_available):
        """Test consumer can start and stop cleanly."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        consumer = FTEKafkaConsumer(
            topics=["fte.metrics"],
            group_id="test-consumer-group"
        )
        
        # Start should not raise
        await consumer.start()
        assert consumer.is_running is True
        
        # Stop should not raise
        await consumer.stop()
        assert consumer.is_running is False

    @pytest.mark.asyncio
    async def test_consume_message(self, kafka_available):
        """Test consuming a message published by producer."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        test_topic = "fte.tickets.incoming"
        received_messages = []
        
        # Create producer and consumer
        producer = FTEKafkaProducer()
        consumer = FTEKafkaConsumer(
            topics=[test_topic],
            group_id=f"test-consumer-{int(time.time())}"
        )
        
        await producer.start()
        await consumer.start()
        
        try:
            # Publish test message
            test_message = {
                "test_id": "consume_test_001",
                "content": "Test consume message",
                "channel": "email"
            }
            await producer.publish(test_topic, test_message)
            
            # Consume messages
            async def handler(topic, msg):
                received_messages.append((topic, msg))
            
            # Run consumer for a short time
            consume_task = asyncio.create_task(consumer.consume(handler))
            await asyncio.sleep(3)
            await consumer.stop()
            
            try:
                await asyncio.wait_for(consume_task, timeout=5)
            except asyncio.TimeoutError:
                pass
            except asyncio.CancelledError:
                pass
            
            # Should have received the message
            assert len(received_messages) > 0, "Should receive at least one message"
            
            # Check message content
            topic, msg = received_messages[0]
            assert topic == test_topic
            assert msg.get("test_id") == "consume_test_001"
            
        finally:
            await producer.stop()


# ============================================================================
# TEST 4: TOPIC TEST
# ============================================================================

class TestKafkaTopics:
    """Test Kafka topic functionality."""

    @pytest.mark.asyncio
    async def test_all_topics_exist(self, kafka_available):
        """Test that all 7 FTE topics exist."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        expected_topics = [
            "fte.tickets.incoming",
            "fte.channels.email.inbound",
            "fte.channels.whatsapp.inbound",
            "fte.channels.webform.inbound",
            "fte.escalations",
            "fte.metrics",
            "fte.dlq"
        ]
        
        for topic in expected_topics:
            exists = await KafkaHealthCheck.check_topic_exists(topic)
            assert exists is True, f"Topic {topic} should exist"

    @pytest.mark.asyncio
    async def test_publish_to_all_topics(self, kafka_available):
        """Test publishing to each topic."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        test_message = {"test": "message", "timestamp": datetime.now().isoformat()}
        
        producer = FTEKafkaProducer()
        try:
            await producer.start()
            
            for topic_name, topic_key in TOPICS.items():
                success = await producer.publish(topic_key, test_message)
                assert success is True, f"Should publish to {topic_key}"
        finally:
            await producer.stop()

    @pytest.mark.asyncio
    async def test_topic_constants(self):
        """Test that TOPICS dict has correct structure."""
        assert isinstance(TOPICS, dict)
        assert len(TOPICS) == 7
        
        # Check all expected keys exist
        expected_keys = [
            "tickets_incoming",
            "email_inbound",
            "whatsapp_inbound",
            "webform_inbound",
            "escalations",
            "metrics",
            "dlq"
        ]
        
        for key in expected_keys:
            assert key in TOPICS, f"TOPICS should have key {key}"
            assert TOPICS[key].startswith("fte."), f"Topic {key} should start with 'fte.'"


# ============================================================================
# TEST 5: FALLBACK TEST
# ============================================================================

class TestKafkaFallback:
    """Test fallback to in-memory queue when Kafka is unavailable."""

    @pytest.mark.asyncio
    async def test_message_queue_fallback_exists(self):
        """Test that in-memory MessageQueue is available."""
        queue = MessageQueue()
        assert queue is not None

    @pytest.mark.asyncio
    async def test_fallback_publish_consume(self):
        """Test publishing and consuming via fallback queue."""
        queue = MessageQueue()
        
        test_topic = KafkaTopics.TICKETS_INCOMING
        test_message = {
            "fallback_test": True,
            "content": "Testing fallback queue"
        }
        
        # Publish to fallback queue
        msg_id = queue.publish(test_topic, test_message)
        assert msg_id is not None
        
        # Consume from fallback queue
        received = []
        
        async def handler(msg):
            received.append(msg)
        
        await queue.consume(test_topic, handler, timeout=2.0)
        
        assert len(received) > 0
        # Message should have the original content
        assert received[0].get("content") == "Testing fallback queue"

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_unavailable(self):
        """Test that health check handles unavailable Kafka gracefully."""
        # Test with invalid server
        result = await KafkaHealthCheck.check_connection(
            bootstrap_servers="invalid-server:9999"
        )
        assert result is False


# ============================================================================
# TEST 6: INTEGRATION TEST
# ============================================================================

class TestKafkaIntegration:
    """Integration tests for full Kafka workflow."""

    @pytest.mark.asyncio
    async def test_full_publish_consume_cycle(self, kafka_available):
        """Test full publish-consume cycle."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        test_topic = "fte.tickets.incoming"
        received = []
        unique_id = f"INT-{int(time.time())}"
        
        producer = FTEKafkaProducer()
        consumer = FTEKafkaConsumer(
            topics=[test_topic],
            group_id=f"integration-test-{unique_id}"
        )
        
        await producer.start()
        await consumer.start()
        
        try:
            # Publish ticket with unique ID
            ticket_data = {
                "ticket_id": unique_id,
                "customer_email": "integration@test.com",
                "channel": "email",
                "content": "Integration test ticket",
                "metadata": {"source": "test"}
            }
            
            publish_success = await producer.publish(test_topic, ticket_data)
            assert publish_success is True
            
            # Consume
            async def handler(topic, msg):
                # Only accept messages with our unique ID
                if msg.get("ticket_id") == unique_id:
                    received.append((topic, msg))
            
            consume_task = asyncio.create_task(consumer.consume(handler))
            await asyncio.sleep(5)
            await consumer.stop()
            
            try:
                await asyncio.wait_for(consume_task, timeout=10)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            
            # Verify received
            assert len(received) > 0, f"Should receive the published ticket with ID {unique_id}"
            
            topic, msg = received[0]
            assert topic == test_topic
            assert msg.get("ticket_id") == unique_id
            assert msg.get("customer_email") == "integration@test.com"
            
        finally:
            await producer.stop()

    @pytest.mark.asyncio
    async def test_metrics_publishing(self, kafka_available):
        """Test publishing metrics to Kafka."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        metrics_topic = "fte.metrics"
        
        metrics_data = {
            "metric_type": "message_processed",
            "channel": "email",
            "latency_ms": 150,
            "escalated": False,
            "tool_calls_count": 3,
            "timestamp": datetime.now().isoformat()
        }
        
        producer = FTEKafkaProducer()
        try:
            await producer.start()
            success = await producer.publish(metrics_topic, metrics_data)
            assert success is True
        finally:
            await producer.stop()

    @pytest.mark.asyncio
    async def test_dlq_publishing(self, kafka_available):
        """Test publishing to Dead Letter Queue."""
        if not kafka_available:
            pytest.skip("Kafka not available")
        
        dlq_topic = "fte.dlq"
        
        dlq_message = {
            "original_message": {"content": "Failed message"},
            "error": "Test error",
            "error_type": "TestError",
            "timestamp": datetime.now().isoformat()
        }
        
        producer = FTEKafkaProducer()
        try:
            await producer.start()
            success = await producer.publish(dlq_topic, dlq_message)
            assert success is True
        finally:
            await producer.stop()


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
