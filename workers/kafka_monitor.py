"""
TechCorp Customer Success AI Agent - Kafka Monitor

Simple monitoring script for Kafka topics.

Run with:
    python workers/kafka_monitor.py
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional

from aiokafka import AIOKafkaConsumer
from kafka.admin import KafkaAdminClient

from kafka_client import TOPICS, KafkaHealthCheck
from production.config import AgentConfig


# ============================================================================
# KAFKA MONITOR
# ============================================================================

class KafkaMonitor:
    """
    Monitor Kafka topics for message activity.
    
    Usage:
        monitor = KafkaMonitor()
        await monitor.monitor_topics()
    """

    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS
        self._running = False
        self._message_counts: Dict[str, int] = {topic: 0 for topic in TOPICS.values()}
        self._last_check: Dict[str, float] = {topic: time.time() for topic in TOPICS.values()}

    def _get_admin_client(self) -> KafkaAdminClient:
        """Create a Kafka admin client."""
        return KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id='fte-kafka-monitor',
            request_timeout_ms=30000
        )

    async def get_topic_message_count(self, topic: str) -> int:
        """
        Get approximate message count for a topic.
        
        Note: This is an estimate based on consumer polling.
        """
        count = 0
        consumer = None
        
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"monitor-{topic.replace('.', '-')}",
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                consumer_timeout_ms=1000
            )
            await consumer.start()
            
            # Count messages for a short period
            async for msg in consumer:
                count += 1
                if count >= 100:  # Limit to 100 messages per check
                    break
                    
        except Exception:
            pass
        finally:
            if consumer:
                try:
                    await consumer.stop()
                except:
                    pass
        
        return count

    def get_topic_status_sync(self) -> Dict[str, Dict]:
        """Get status of all topics using sync admin client."""
        admin_client = None
        status = {}
        
        try:
            admin_client = self._get_admin_client()
            existing_topics = set(admin_client.list_topics())
            
            for topic_name, topic_key in TOPICS.items():
                status[topic_key] = {
                    "exists": topic_key in existing_topics,
                    "messages_seen": self._message_counts.get(topic_key, 0),
                    "last_check": self._last_check.get(topic_key, 0)
                }
                
        except Exception as e:
            status["error"] = str(e)
        finally:
            if admin_client:
                try:
                    admin_client.close()
                except:
                    pass
        
        return status

    async def monitor_topics(self, interval: int = 5) -> None:
        """
        Monitor topics and print status periodically.
        
        Args:
            interval: Seconds between status updates.
        """
        self._running = True
        
        print("=" * 70)
        print("Kafka Topic Monitor")
        print("=" * 70)
        print(f"Bootstrap servers: {self.bootstrap_servers}")
        print(f"Update interval: {interval} seconds")
        print("Press Ctrl+C to stop")
        print("=" * 70)
        
        # Check initial connection
        connected = await KafkaHealthCheck.check_connection(self.bootstrap_servers)
        if not connected:
            print("ERROR: Cannot connect to Kafka")
            return
        
        print("\nMonitoring started...\n")
        
        try:
            while self._running:
                status = self.get_topic_status_sync()
                
                print(f"\n{'='*70}")
                print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*70}")
                print(f"{'Topic':<40} {'Exists':<8} {'Messages':<10}")
                print(f"{'-'*70}")
                
                for topic_key, info in status.items():
                    if topic_key == "error":
                        print(f"ERROR: {info}")
                        continue
                    
                    exists_str = "Yes" if info.get("exists") else "No"
                    msg_count = info.get("messages_seen", 0)
                    print(f"{topic_key:<40} {exists_str:<8} {msg_count:<10}")
                
                # Calculate processing rate
                current_time = time.time()
                print(f"\n{'-'*70}")
                print("Processing Rate (messages/second):")
                
                for topic_key in TOPICS.values():
                    info = status.get(topic_key, {})
                    last_count = info.get("messages_seen", 0)
                    last_check = info.get("last_check", current_time)
                    
                    time_diff = current_time - last_check
                    if time_diff > 0:
                        rate = last_count / time_diff
                        print(f"  {topic_key}: {rate:.2f}/s")
                
                # Update tracking
                for topic_key in TOPICS.values():
                    self._last_check[topic_key] = current_time
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            print("\nMonitor cancelled")
        except KeyboardInterrupt:
            print("\nMonitor stopped by user")
        finally:
            self._running = False

    def stop(self) -> None:
        """Stop the monitor."""
        self._running = False


async def show_recent_messages(
    topic: str,
    count: int = 5,
    bootstrap_servers: str = None
) -> List[Dict]:
    """
    Show last N messages from a topic.
    
    Args:
        topic: Topic name to read from.
        count: Number of messages to retrieve.
        bootstrap_servers: Kafka bootstrap servers.
        
    Returns:
        List of message dictionaries.
    """
    servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS
    messages = []
    
    consumer = None
    try:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=servers,
            group_id=f"monitor-reader-{int(time.time())}",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            consumer_timeout_ms=2000,
            max_poll_records=count
        )
        await consumer.start()
        
        async for msg in consumer:
            messages.append({
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "key": msg.key,
                "value": msg.value,
                "timestamp": msg.timestamp
            })
            
            if len(messages) >= count:
                break
                
    except Exception as e:
        print(f"Error reading messages: {e}")
    finally:
        if consumer:
            try:
                await consumer.stop()
            except:
                pass
    
    return messages


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the Kafka monitor."""
    monitor = KafkaMonitor()
    await monitor.monitor_topics(interval=5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped")
