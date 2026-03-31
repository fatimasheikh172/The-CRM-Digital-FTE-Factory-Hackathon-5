"""
Test cases for TechCorp Customer Success AI Agent Prototype.

Tests cover all 8 sample tickets and verify:
- Correct channel handling
- Proper sentiment analysis
- Accurate escalation decisions
- Channel-specific formatting
"""

import json
import unittest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.prototype import CustomerSuccessAgent, process_ticket


class TestCustomerSuccessAgent(unittest.TestCase):
    """Test cases for the Customer Success Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = CustomerSuccessAgent()
        
        # Load sample tickets
        # Path: tests/ -> parent is hackhaton-5/ -> context/
        tickets_path = Path(__file__).parent.parent / "context" / "sample-tickets.json"
        with open(tickets_path, 'r', encoding='utf-8') as f:
            self.tickets = json.load(f)
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly with all skills."""
        self.assertIsNotNone(self.agent.knowledge_skill)
        self.assertIsNotNone(self.agent.sentiment_skill)
        self.assertIsNotNone(self.agent.escalation_skill)
        self.assertIsNotNone(self.agent.channel_skill)
        self.assertIsNotNone(self.agent.customer_skill)
    
    def test_email_channel_handling(self):
        """Test email channel processing (Ticket #1)."""
        ticket = self.tickets[0]  # Login issue
        response = process_ticket(self.agent, ticket)
        
        self.assertEqual(response.channel_used, 'email')
        self.assertFalse(response.should_escalate)  # Login issues shouldn't escalate
        self.assertIn('Dear', response.response_text)  # Email greeting
        self.assertIn('Best regards', response.response_text)  # Email signature
    
    def test_whatsapp_channel_handling(self):
        """Test WhatsApp channel processing (Ticket #2)."""
        ticket = self.tickets[1]  # App not working
        response = process_ticket(self.agent, ticket)
        
        self.assertEqual(response.channel_used, 'whatsapp')
        self.assertFalse(response.should_escalate)  # Vague issue, ask for details first
        # WhatsApp should be relatively short (under 300 chars)
        self.assertLess(len(response.response_text), 300)
    
    def test_web_form_channel_handling(self):
        """Test web form channel processing (Ticket #3)."""
        ticket = self.tickets[2]  # API rate limit
        response = process_ticket(self.agent, ticket)
        
        self.assertEqual(response.channel_used, 'web_form')
        self.assertFalse(response.should_escalate)  # API questions shouldn't escalate
        self.assertIn('Hello', response.response_text)  # Web form greeting
    
    def test_refund_escalation(self):
        """Test refund request triggers escalation (Ticket #4)."""
        ticket = self.tickets[3]  # Refund request
        response = process_ticket(self.agent, ticket)
        
        self.assertTrue(response.should_escalate)
        self.assertEqual(response.escalation_reason, 'Customer requested refund')
    
    def test_pricing_inquiry_no_escalation(self):
        """Test pricing inquiry doesn't escalate (Ticket #5)."""
        ticket = self.tickets[4]  # Pricing question
        response = process_ticket(self.agent, ticket)
        
        self.assertFalse(response.should_escalate)
        self.assertEqual(response.channel_used, 'whatsapp')
    
    def test_api_docs_request(self):
        """Test API documentation request (Ticket #6)."""
        ticket = self.tickets[5]  # API docs
        response = process_ticket(self.agent, ticket)
        
        self.assertFalse(response.should_escalate)
        self.assertIn('API', response.response_text)
    
    def test_new_customer_onboarding(self):
        """Test new customer getting started (Ticket #7)."""
        ticket = self.tickets[6]  # Getting started
        response = process_ticket(self.agent, ticket)
        
        self.assertFalse(response.should_escalate)
        self.assertEqual(response.channel_used, 'email')
        # Should identify as existing customer (in simulated DB)
        self.assertFalse(response.is_new_customer)
    
    def test_human_agent_request_escalation(self):
        """Test human agent request triggers escalation (Ticket #8)."""
        ticket = self.tickets[7]  # Human agent request
        response = process_ticket(self.agent, ticket)
        
        self.assertTrue(response.should_escalate)
        self.assertEqual(response.escalation_reason, 'Customer requested human agent')
    
    def test_sentiment_analysis_positive(self):
        """Test sentiment analysis with positive message."""
        result = self.agent.sentiment_skill.analyze("This is great! I love your product!")
        self.assertGreater(result['score'], 0.6)
        self.assertEqual(result['label'], 'positive')
    
    def test_sentiment_analysis_negative(self):
        """Test sentiment analysis with negative message."""
        result = self.agent.sentiment_skill.analyze("This is terrible and broken!")
        self.assertLess(result['score'], 0.4)
        self.assertEqual(result['label'], 'negative')
    
    def test_sentiment_analysis_neutral(self):
        """Test sentiment analysis with neutral message."""
        result = self.agent.sentiment_skill.analyze("How do I reset my password?")
        self.assertGreaterEqual(result['score'], 0.4)
        self.assertLessEqual(result['score'], 0.6)
        self.assertEqual(result['label'], 'neutral')
    
    def test_customer_identification_existing(self):
        """Test identifying existing customer by email."""
        result = self.agent.customer_skill.identify(email='john@example.com')
        self.assertFalse(result['is_new_customer'])
        self.assertEqual(result['customer_id'], 'CUST-001')
    
    def test_customer_identification_new(self):
        """Test identifying new customer."""
        result = self.agent.customer_skill.identify(email='unknown@example.com')
        self.assertTrue(result['is_new_customer'])
        self.assertTrue(result['customer_id'].startswith('NEW-'))
    
    def test_knowledge_retrieval(self):
        """Test knowledge base search."""
        results = self.agent.knowledge_skill.search('password reset')
        self.assertGreater(len(results), 0)
        self.assertIn('Password Reset', results[0]['title'])
    
    def test_channel_formatting_email(self):
        """Test email response formatting."""
        response = self.agent.channel_skill.format_response(
            "Here is the solution to your problem.",
            'email',
            customer_name='John'
        )
        self.assertIn('Dear John,', response)
        self.assertIn('Best regards', response)
    
    def test_channel_formatting_whatsapp(self):
        """Test WhatsApp response formatting."""
        response = self.agent.channel_skill.format_response(
            "Here is the solution to your problem. Let me know if you need help.",
            'whatsapp'
        )
        # Should be short
        self.assertLess(len(response.split('.')), 4)
    
    def test_channel_formatting_web_form(self):
        """Test web form response formatting."""
        response = self.agent.channel_skill.format_response(
            "Here is the solution to your problem.",
            'web_form',
            customer_name='Jane'
        )
        self.assertIn('Hello Jane,', response)
        self.assertIn('Thank you for contacting TechCorp Support', response)
    
    def test_all_tickets_processed(self):
        """Test that all 8 tickets can be processed without errors."""
        for ticket in self.tickets:
            response = process_ticket(self.agent, ticket)
            self.assertIsNotNone(response.response_text)
            self.assertIsInstance(response.sentiment_score, float)
            self.assertIsInstance(response.should_escalate, bool)
    
    def test_escalation_rate(self):
        """Test expected escalation rate on sample tickets."""
        escalation_count = 0
        for ticket in self.tickets:
            response = process_ticket(self.agent, ticket)
            if response.should_escalate:
                escalation_count += 1
        
        # Expected: 2 escalations (tickets #4 and #8)
        self.assertEqual(escalation_count, 2)
    
    def test_processing_time(self):
        """Test that processing time is reasonable."""
        for ticket in self.tickets:
            response = process_ticket(self.agent, ticket)
            # Should process in under 100ms
            self.assertLess(response.processing_time_ms, 100)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = CustomerSuccessAgent()
    
    def test_empty_message(self):
        """Test handling of empty message."""
        response = self.agent.process_message(
            message='',
            channel='email',
            customer_email='test@example.com'
        )
        self.assertTrue(response.should_escalate)  # Error should escalate
        self.assertIn('Error', response.escalation_reason)
    
    def test_unknown_channel(self):
        """Test handling of unknown channel."""
        response = self.agent.process_message(
            message='Hello',
            channel='unknown_channel',
            customer_email='test@example.com'
        )
        self.assertTrue(response.should_escalate)  # Error should escalate
    
    def test_all_caps_angry_message(self):
        """Test handling of ALL CAPS angry message."""
        response = self.agent.process_message(
            message='I WANT THIS FIXED NOW!!!',
            channel='whatsapp',
            customer_phone='+1234567890'
        )
        # Should detect negative sentiment
        self.assertLessEqual(response.sentiment_score, 0.4)
    
    def test_legal_threat_escalation(self):
        """Test escalation for legal threats."""
        response = self.agent.process_message(
            message="I'm going to contact my lawyer about this",
            channel='email',
            customer_email='test@example.com'
        )
        self.assertTrue(response.should_escalate)
        self.assertIn('legal', response.escalation_reason.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)
