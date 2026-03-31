"""
TechCorp Customer Success AI Agent - Kafka Topic Setup

Script to create all required Kafka topics for the FTE system.
Uses kafka-python with proper timeout configuration.

Run with:
    python kafka_setup.py
"""

import time
import logging
from typing import Dict

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaTimeoutError

from production.config import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# KAFKA TOPICS CONFIGURATION
# ============================================================================

TOPICS_CONFIG = {
    "fte.tickets.incoming": {"partitions": 3, "replication_factor": 1},
    "fte.channels.email.inbound": {"partitions": 1, "replication_factor": 1},
    "fte.channels.whatsapp.inbound": {"partitions": 1, "replication_factor": 1},
    "fte.channels.webform.inbound": {"partitions": 1, "replication_factor": 1},
    "fte.escalations": {"partitions": 1, "replication_factor": 1},
    "fte.metrics": {"partitions": 1, "replication_factor": 1},
    "fte.dlq": {"partitions": 1, "replication_factor": 1},
}


# ============================================================================
# KAFKA TOPIC SETUP
# ============================================================================

class KafkaTopicSetup:
    """
    Creates and manages Kafka topics for the FTE system.
    """

    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or AgentConfig.KAFKA_BOOTSTRAP_SERVERS

    def _get_admin_client(self) -> KafkaAdminClient:
        """Create a Kafka admin client with proper configuration."""
        return KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id='fte-kafka-setup',
            request_timeout_ms=60000,
            api_version_auto_timeout_ms=30000,
            connections_max_idle_ms=60000
        )

    def create_topics(self) -> Dict[str, dict]:
        """Create all required Kafka topics."""
        logger.info(f"Connecting to Kafka at {self.bootstrap_servers}")
        results = {}
        
        admin_client = None
        try:
            admin_client = self._get_admin_client()
            
            # Get existing topics with retry
            existing_topics = set()
            for attempt in range(3):
                try:
                    existing_topics = set(admin_client.list_topics())
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(2)
            
            logger.info(f"Existing topics: {existing_topics}")
            
            # Create topics that don't exist
            topics_to_create = []
            for topic_name, config in TOPICS_CONFIG.items():
                if topic_name in existing_topics:
                    logger.info(f"Topic already exists: {topic_name}")
                    results[topic_name] = {"created": False, "existed": True}
                else:
                    new_topic = NewTopic(
                        name=topic_name,
                        num_partitions=config["partitions"],
                        replication_factor=config["replication_factor"]
                    )
                    topics_to_create.append(new_topic)
            
            if topics_to_create:
                logger.info(f"Creating {len(topics_to_create)} new topics...")
                create_futures = admin_client.create_topics(
                    topics_to_create,
                    validate_only=False
                )
                
                for topic_name, future in create_futures.items():
                    try:
                        future.result(timeout=30)
                        logger.info(f"Created topic: {topic_name}")
                        results[topic_name] = {"created": True, "existed": False}
                    except TopicAlreadyExistsError:
                        logger.info(f"Topic already exists: {topic_name}")
                        results[topic_name] = {"created": False, "existed": True}
                    except Exception as e:
                        logger.error(f"Failed to create topic {topic_name}: {e}")
                        results[topic_name] = {"created": False, "existed": False, "error": str(e)}
            else:
                logger.info("All topics already exist")
                
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
            for topic_name in TOPICS_CONFIG:
                if topic_name not in results:
                    results[topic_name] = {"created": False, "existed": False, "error": str(e)}
        finally:
            if admin_client:
                try:
                    admin_client.close()
                except:
                    pass
        
        return results

    def verify_topics(self) -> bool:
        """Check all required topics exist."""
        admin_client = None
        try:
            admin_client = self._get_admin_client()
            existing_topics = set(admin_client.list_topics())
            
            missing_topics = [t for t in TOPICS_CONFIG if t not in existing_topics]
            
            if missing_topics:
                logger.warning(f"Missing topics: {missing_topics}")
                return False
            
            logger.info("All required topics exist")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying topics: {e}")
            return False
        finally:
            if admin_client:
                try:
                    admin_client.close()
                except:
                    pass

    def get_topic_status(self) -> Dict[str, dict]:
        """Get status of all FTE topics."""
        admin_client = None
        try:
            admin_client = self._get_admin_client()
            existing_topics = set(admin_client.list_topics())
            
            status = {}
            for topic_name, config in TOPICS_CONFIG.items():
                status[topic_name] = {
                    "configured_partitions": config["partitions"],
                    "configured_replication": config["replication_factor"],
                    "exists": topic_name in existing_topics,
                    "actual_partitions": 0,
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting topic status: {e}")
            return {}
        finally:
            if admin_client:
                try:
                    admin_client.close()
                except:
                    pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the Kafka topic setup."""
    print("=" * 60)
    print("Kafka Topic Setup")
    print("=" * 60)
    
    setup = KafkaTopicSetup()
    
    # Check connection
    print("\n1. Checking Kafka connection...")
    admin_client = None
    try:
        print("   Attempting to connect (this may take a moment)...")
        admin_client = setup._get_admin_client()
        topics = set(admin_client.list_topics())
        print(f"   Connected successfully")
        print(f"   Found {len(topics)} topics")
    except Exception as e:
        print(f"   ERROR: Cannot connect to Kafka: {e}")
        print("   Make sure Kafka is running on localhost:9092")
        return False
    finally:
        if admin_client:
            try:
                admin_client.close()
            except:
                pass
    
    # Create topics
    print("\n2. Creating topics...")
    results = setup.create_topics()
    
    created_count = 0
    existed_count = 0
    failed_count = 0
    
    for topic_name, result in results.items():
        if result.get("created"):
            print(f"   ✓ Created: {topic_name}")
            created_count += 1
        elif result.get("existed"):
            print(f"   - Exists: {topic_name}")
            existed_count += 1
        else:
            print(f"   ✗ Failed: {topic_name} - {result.get('error', 'Unknown error')}")
            failed_count += 1
    
    print(f"\n   Summary: {created_count} created, {existed_count} existed, {failed_count} failed")
    
    # Verify topics
    print("\n3. Verifying topics...")
    verified = setup.verify_topics()
    
    if verified:
        print("   ✓ All required topics verified")
    else:
        print("   ✗ Some topics are missing")
    
    # Show topic status
    print("\n4. Topic status:")
    status = setup.get_topic_status()
    for topic_name, info in status.items():
        exists_str = "Yes" if info["exists"] else "No"
        partitions = info["actual_partitions"] if info["exists"] else info["configured_partitions"]
        print(f"   {topic_name}:")
        print(f"      Exists: {exists_str}")
        print(f"      Partitions: {partitions}")
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    
    return verified


if __name__ == "__main__":
    result = main()
    exit(0 if result else 1)
