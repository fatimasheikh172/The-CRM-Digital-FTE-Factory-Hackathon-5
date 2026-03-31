"""
Test cases for Memory and State Management System.

Tests cover:
1. New Customer First Contact
2. Returning Customer Same Channel
3. Cross-Channel Recognition
4. Sentiment Tracking
5. Topic Tracking
6. Status Transitions
"""

import json
import unittest
import shutil
from pathlib import Path
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.memory import ConversationMemory, ConversationStatus, SentimentTrend, ResolutionStatus
from src.agent.customer_db import CustomerDatabase


class TestConversationMemory(unittest.TestCase):
    """Test cases for ConversationMemory class."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.memory = ConversationMemory(
            customer_id="test@example.com",
            storage_dir=str(self.test_dir)
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_add_message(self):
        """Test adding a message to conversation."""
        self.memory.add_message("customer", "Hello, I need help", "email", 0.5)
        
        history = self.memory.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['role'], "customer")
        self.assertEqual(history[0]['content'], "Hello, I need help")
        self.assertEqual(history[0]['channel'], "email")
        self.assertEqual(history[0]['sentiment_score'], 0.5)
    
    def test_get_summary(self):
        """Test getting conversation summary."""
        self.memory.add_message("customer", "Hello", "email", 0.5)
        self.memory.add_message("agent", "How can I help?", "email", 0.5)
        
        summary = self.memory.get_summary()
        
        self.assertIn("test@example.com", summary)
        self.assertIn("Messages:", summary)
        self.assertIn("Channels:", summary)
    
    def test_update_status(self):
        """Test updating conversation status."""
        self.memory.update_status("active")
        self.assertEqual(self.memory.get_status(), "active")
        
        self.memory.update_status("resolved")
        self.assertEqual(self.memory.get_status(), "resolved")
        
        self.memory.update_status("escalated")
        self.assertEqual(self.memory.get_status(), "escalated")
    
    def test_add_topic(self):
        """Test adding topics to conversation."""
        self.memory.add_topic("login")
        self.memory.add_topic("billing")
        
        topics = self.memory.get_topics_discussed()
        
        self.assertIn("login", topics)
        self.assertIn("billing", topics)
        self.assertEqual(len(topics), 2)
    
    def test_update_sentiment_trend(self):
        """Test sentiment trend calculation."""
        # Add improving sentiment
        self.memory.add_message("customer", "Message 1", "email", 0.3)
        self.memory.add_message("customer", "Message 2", "email", 0.5)
        self.memory.add_message("customer", "Message 3", "email", 0.7)
        self.memory.update_sentiment_trend()
        
        trend = self.memory.get_sentiment_trend()
        self.assertEqual(trend, "improving")
    
    def test_switch_channel(self):
        """Test channel switching detection."""
        self.memory.switch_channel("email")
        context = self.memory.get_customer_context()
        
        self.assertEqual(context['customer_state']['current_channel'], "email")
        self.assertEqual(context['customer_state']['first_contact_channel'], "email")
        self.assertFalse(context['customer_state']['has_switched_channels'])
        
        # Switch to different channel
        self.memory.switch_channel("whatsapp")
        context = self.memory.get_customer_context()
        
        self.assertTrue(context['customer_state']['has_switched_channels'])
        self.assertEqual(context['customer_state']['current_channel'], "whatsapp")
    
    def test_is_same_customer(self):
        """Test customer identity check."""
        self.assertTrue(self.memory.is_same_customer("test@example.com"))
        self.assertTrue(self.memory.is_same_customer("TEST@EXAMPLE.COM"))  # Case insensitive
        self.assertFalse(self.memory.is_same_customer("other@example.com"))
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        self.memory.add_message("customer", "Hello", "email", 0.5)
        self.memory.add_topic("login")
        
        # Serialize
        data = self.memory.to_dict()
        
        # Deserialize
        restored = ConversationMemory.from_dict(data, str(self.test_dir))
        
        self.assertEqual(restored.customer_id, self.memory.customer_id)
        self.assertEqual(len(restored.get_history()), 1)
        self.assertEqual(restored.get_topics_discussed(), ["login"])


class TestCustomerDatabase(unittest.TestCase):
    """Test cases for CustomerDatabase class."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.db = CustomerDatabase(str(self.test_dir))
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_customer(self):
        """Test creating a new customer."""
        customer = self.db.create_customer("new@example.com", "email")
        
        self.assertIsNotNone(customer['customer_id'])
        self.assertEqual(customer['email'], "new@example.com")
        self.assertEqual(customer['first_channel'], "email")
        self.assertEqual(customer['total_conversations'], 0)
    
    def test_find_customer_by_email(self):
        """Test finding customer by email."""
        self.db.create_customer("find@example.com", "email")
        
        customer = self.db.find_customer(email="find@example.com")
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer['email'], "find@example.com")
    
    def test_find_customer_by_phone(self):
        """Test finding customer by phone."""
        self.db.create_customer("+1234567890", "whatsapp")
        
        customer = self.db.find_customer(phone="+1234567890")
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer['phone'], "+1234567890")
    
    def test_get_or_create_customer_existing(self):
        """Test get_or_create with existing customer."""
        self.db.create_customer("existing@example.com", "email")
        
        customer = self.db.get_or_create_customer("existing@example.com", "email")
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer['email'], "existing@example.com")
    
    def test_get_or_create_customer_new(self):
        """Test get_or_create with new customer."""
        customer = self.db.get_or_create_customer("brandnew@example.com", "web_form")
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer['email'], "brandnew@example.com")
    
    def test_save_conversation(self):
        """Test saving a conversation."""
        customer = self.db.create_customer("conv@example.com", "email")
        
        conversation = {
            'conversation_id': 'CONV-TEST123',
            'messages': [{'role': 'customer', 'content': 'Hello'}],
            'customer_state': {'customer_id': customer['customer_id']},
            'conversation_state': {'status': 'active'}
        }
        
        conv_id = self.db.save_conversation(customer['customer_id'], conversation)
        
        self.assertEqual(conv_id, 'CONV-TEST123')
        
        # Verify customer was updated
        updated_customer = self.db.find_customer(email="conv@example.com")
        self.assertEqual(updated_customer['total_conversations'], 1)
    
    def test_get_customer_history(self):
        """Test retrieving customer conversation history."""
        customer = self.db.create_customer("history@example.com", "email")
        
        # Save multiple conversations
        for i in range(3):
            conv = {
                'conversation_id': f'CONV-{i}',
                'messages': [],
                'customer_state': {},
                'conversation_state': {'status': 'active'}
            }
            self.db.save_conversation(customer['customer_id'], conv)
        
        history = self.db.get_customer_history(customer['customer_id'])
        
        self.assertEqual(len(history), 3)
    
    def test_update_conversation(self):
        """Test updating a conversation."""
        customer = self.db.create_customer("update@example.com", "email")
        
        conv = {
            'conversation_id': 'CONV-UPDATE',
            'messages': [],
            'customer_state': {},
            'conversation_state': {'status': 'active'}
        }
        self.db.save_conversation(customer['customer_id'], conv)
        
        # Update
        self.db.update_conversation('CONV-UPDATE', {
            'data': {'conversation_state': {'status': 'resolved'}}
        })
        
        updated = self.db.get_conversation('CONV-UPDATE')
        self.assertEqual(updated['data']['conversation_state']['status'], 'resolved')
    
    def test_get_active_conversation(self):
        """Test getting active conversation."""
        customer = self.db.create_customer("active@example.com", "email")
        
        # Save resolved conversation
        conv1 = {
            'conversation_id': 'CONV-RESOLVED',
            'messages': [],
            'customer_state': {},
            'conversation_state': {'status': 'resolved'}
        }
        self.db.save_conversation(customer['customer_id'], conv1)
        
        # Save active conversation
        conv2 = {
            'conversation_id': 'CONV-ACTIVE',
            'messages': [],
            'customer_state': {},
            'conversation_state': {'status': 'active'}
        }
        self.db.save_conversation(customer['customer_id'], conv2)
        
        active = self.db.get_active_conversation(customer['customer_id'])
        
        self.assertEqual(active['conversation_id'], 'CONV-ACTIVE')
    
    def test_get_stats(self):
        """Test getting database statistics."""
        self.db.create_customer("stat1@example.com", "email")
        self.db.create_customer("stat2@example.com", "whatsapp")
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_customers'], 2)
        self.assertEqual(stats['total_conversations'], 0)


class TestMemoryScenarios(unittest.TestCase):
    """Integration tests for memory scenarios."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.db = CustomerDatabase(str(self.test_dir))
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_scenario_1_new_customer_first_contact(self):
        """TEST 1 - New Customer First Contact."""
        # Create memory for new customer
        memory = ConversationMemory("newcustomer@example.com", str(self.test_dir))
        
        # Add first message
        memory.add_message("customer", "I need help with login", "email", 0.5)
        memory.add_topic("login")
        
        # Save to database
        customer = self.db.get_or_create_customer("newcustomer@example.com", "email")
        self.db.save_conversation(customer['customer_id'], memory.to_dict())
        
        # Verify customer created
        self.assertFalse(customer['email'] is None)
        self.assertEqual(customer['first_channel'], "email")
        
        # Verify conversation saved
        history = self.db.get_customer_history(customer['customer_id'])
        self.assertEqual(len(history), 1)
    
    def test_scenario_2_returning_customer_same_channel(self):
        """TEST 2 - Returning Customer Same Channel."""
        # First contact
        memory1 = ConversationMemory("returning@example.com", str(self.test_dir))
        memory1.add_message("customer", "How do I reset password?", "email", 0.5)
        memory1.add_topic("login")
        
        customer = self.db.get_or_create_customer("returning@example.com", "email")
        self.db.save_conversation(customer['customer_id'], memory1.to_dict())
        
        # Second contact (follow-up)
        memory2 = ConversationMemory("returning@example.com", str(self.test_dir))
        memory2.add_message("customer", "Thanks, that worked!", "email", 0.8)
        
        # Check if returning customer
        context = memory2.get_customer_context()
        
        # Verify history exists
        history = self.db.get_customer_history(customer['customer_id'])
        self.assertEqual(len(history), 1)  # Previous conversation
    
    def test_scenario_3_cross_channel_recognition(self):
        """TEST 3 - Cross Channel Recognition."""
        # First contact via email about password reset
        memory1 = ConversationMemory("crosschannel@example.com", str(self.test_dir))
        memory1.add_message("customer", "I need help with password reset", "email", 0.5)
        memory1.add_topic("login")
        memory1.switch_channel("email")
        
        customer = self.db.get_or_create_customer("crosschannel@example.com", "email")
        self.db.save_conversation(customer['customer_id'], memory1.to_dict())
        
        # Verify customer record shows channel switch capability
        updated_customer = self.db.get_or_create_customer("crosschannel@example.com", "whatsapp")
        
        # Verify customer has used multiple channels
        self.assertIn("email", updated_customer.get('channels_used', []))
        self.assertIn("whatsapp", updated_customer.get('channels_used', []))
        
        # Second contact via WhatsApp - new memory instance
        memory2 = ConversationMemory("crosschannel@example.com", str(self.test_dir))
        memory2.add_message("customer", "Still having issues", "whatsapp", 0.4)
        memory2.switch_channel("whatsapp")
        
        # Verify new memory is set up for whatsapp
        context = memory2.get_customer_context()
        self.assertEqual(context['customer_state']['current_channel'], "whatsapp")
    
    def test_scenario_4_sentiment_tracking(self):
        """TEST 4 - Sentiment Tracking."""
        memory = ConversationMemory("sentiment@example.com", str(self.test_dir))
        
        # Start with low sentiment (frustrated)
        memory.add_message("customer", "This is not working!", "email", 0.2)
        self.assertEqual(memory.get_sentiment_trend(), "stable")
        
        # Add more frustrated messages
        memory.add_message("customer", "Still broken", "email", 0.2)
        
        # Then improving
        memory.add_message("customer", "Getting better", "email", 0.5)
        memory.add_message("customer", "Much better now", "email", 0.7)
        memory.add_message("customer", "Great, it works now!", "email", 0.9)
        
        trend = memory.get_sentiment_trend()
        self.assertEqual(trend, "improving")
    
    def test_scenario_5_topic_tracking(self):
        """TEST 5 - Topic Tracking."""
        memory = ConversationMemory("topics@example.com", str(self.test_dir))
        
        # Message about API
        memory.add_message("customer", "API rate limit is too low", "web_form", 0.5)
        memory.add_topic("api")
        
        # Message about billing
        memory.add_message("customer", "How much is the pro plan?", "web_form", 0.5)
        memory.add_topic("pricing")
        
        topics = memory.get_topics_discussed()
        
        self.assertIn("api", topics)
        self.assertIn("pricing", topics)
        self.assertEqual(len(topics), 2)
    
    def test_scenario_6_status_transitions(self):
        """TEST 6 - Status Transitions."""
        memory = ConversationMemory("status@example.com", str(self.test_dir))
        
        # Start active
        self.assertEqual(memory.get_status(), "active")
        
        # Resolve issue
        memory.update_status("resolved")
        self.assertEqual(memory.get_status(), "resolved")
        
        # Reopen and escalate
        memory.update_status("active")
        memory.update_status("escalated")
        self.assertEqual(memory.get_status(), "escalated")
        
        # Verify resolution status updated
        context = memory.get_customer_context()
        self.assertEqual(
            context['conversation_state']['resolution_status'],
            "escalated"
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
