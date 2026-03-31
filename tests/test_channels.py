"""
Channel Integration Tests for TechCorp Customer Success AI Agent.

Tests cover:
1. Gmail Handler - Email processing and formatting
2. WhatsApp Handler - Message processing and formatting
3. Web Form Handler - Form validation and processing
4. Base Channel - Common functionality
5. Cross Channel Format - Different formatting per channel

Run with: pytest tests/test_channels.py -v
"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from channels.base_channel import BaseChannel
from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from channels.web_form_handler import WebFormHandler, SupportFormSubmission, SupportCategory, PriorityLevel


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def gmail_handler():
    """Create Gmail handler in simulation mode."""
    return GmailHandler(simulation_mode=True)


@pytest.fixture
def whatsapp_handler():
    """Create WhatsApp handler in simulation mode."""
    return WhatsAppHandler(simulation_mode=True)


@pytest.fixture
def web_form_handler():
    """Create Web Form handler."""
    return WebFormHandler()


@pytest.fixture
def sample_email():
    """Sample email data for testing."""
    return {
        "from": "John Smith <john.smith@example.com>",
        "subject": "Cannot login to my account",
        "body": "Hi TechCorp Support,\n\nI've been trying to log in to my account for the past hour but keep getting an error message.\n\nThanks,\nJohn",
        "message_id": "TEST-EMAIL-001",
        "thread_id": "thread_001",
        "received_at": "2026-03-15T10:30:00",
        "has_attachment": False
    }


@pytest.fixture
def sample_whatsapp():
    """Sample WhatsApp message for testing."""
    return {
        "from": "whatsapp:+14155551234",
        "to": "whatsapp:+14155559999",
        "body": "hi my app is not working",
        "message_sid": "SM-TEST001",
        "conversation_sid": "CH-001",
        "timestamp": "2026-03-15T09:15:00"
    }


@pytest.fixture
def sample_web_form():
    """Sample web form data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Support Request",
        "category": "Technical",
        "priority": "medium",
        "message": "This is a test message for the support form. It has enough characters."
    }


# ============================================================================
# TEST 1: Gmail Handler
# ============================================================================

class TestGmailHandler:
    """Test Gmail handler functionality."""
    
    def test_process_incoming_email(self, gmail_handler, sample_email):
        """Test processing incoming email."""
        normalized = gmail_handler.process_incoming_email(sample_email)
        
        assert normalized['channel'] == 'email'
        assert normalized['customer_email'] == 'john.smith@example.com'
        assert normalized['customer_name'] == 'John Smith'
        assert normalized['subject'] == 'Cannot login to my account'
        assert 'log in' in normalized['content'].lower() or 'login' in normalized['content'].lower()
        assert normalized['channel_message_id'] == 'TEST-EMAIL-001'
    
    def test_normalized_format_correct(self, gmail_handler, sample_email):
        """Test normalized format has all required fields."""
        normalized = gmail_handler.normalize_message(sample_email)
        
        required_fields = [
            'channel', 'customer_email', 'customer_phone', 'customer_name',
            'subject', 'content', 'channel_message_id', 'received_at', 'metadata'
        ]
        
        for field in required_fields:
            assert field in normalized, f"Missing field: {field}"
    
    def test_send_reply_saves_to_file(self, gmail_handler, tmp_path):
        """Test send_reply saves to simulation file."""
        gmail_handler.simulation_dir = tmp_path
        
        result = gmail_handler.send_reply(
            to_email="test@example.com",
            subject="Re: Test",
            body="Test response body"
        )
        
        assert result['delivery_status'] == 'simulated'
        assert 'channel_message_id' in result
        
        # Check file was created
        sent_file = tmp_path / "gmail_sent.json"
        assert sent_file.exists()
        
        with open(sent_file, 'r') as f:
            sent_emails = json.load(f)
        
        assert len(sent_emails) == 1
        assert sent_emails[0]['to'] == 'test@example.com'
    
    def test_format_response_has_greeting_and_signature(self, gmail_handler):
        """Test formatted email has greeting and signature."""
        response = gmail_handler.format_response(
            "Here is the solution to your problem.",
            {"name": "John"}
        )
        
        assert "Dear John," in response
        assert "Best regards," in response
        assert "TechCorp Support Team" in response
    
    def test_email_response_under_500_words(self, gmail_handler):
        """Test email response is under 500 words."""
        long_text = "word " * 600  # 600 words
        response = gmail_handler.format_response(long_text, {"name": "Test"})
        
        word_count = len(response.split())
        assert word_count <= gmail_handler.max_response_words + 20  # Allow for greeting/signature
    
    def test_validate_incoming_valid(self, gmail_handler):
        """Test validation accepts valid email."""
        valid_email = {
            "from": "test@example.com",
            "body": "This is a valid message body."
        }
        assert gmail_handler.validate_incoming(valid_email) is True
    
    def test_validate_incoming_invalid(self, gmail_handler):
        """Test validation rejects invalid email."""
        # Missing from
        assert gmail_handler.validate_incoming({"body": "test"}) is False
        
        # Missing body
        assert gmail_handler.validate_incoming({"from": "test@example.com"}) is False
        
        # Invalid email format
        assert gmail_handler.validate_incoming({"from": "invalid", "body": "test"}) is False
    
    def test_extract_email_from_header(self, gmail_handler):
        """Test email extraction from header."""
        # Name <email> format
        assert gmail_handler.extract_email_from_header("John <john@example.com>") == "john@example.com"
        
        # Just email
        assert gmail_handler.extract_email_from_header("john@example.com") == "john@example.com"
        
        # Empty
        assert gmail_handler.extract_email_from_header("") == ""


# ============================================================================
# TEST 2: WhatsApp Handler
# ============================================================================

class TestWhatsAppHandler:
    """Test WhatsApp handler functionality."""
    
    def test_process_webhook(self, whatsapp_handler, sample_whatsapp):
        """Test processing WhatsApp webhook."""
        normalized = whatsapp_handler.process_webhook(sample_whatsapp)
        
        assert normalized['channel'] == 'whatsapp'
        assert normalized['customer_phone'] == '+14155551234'
        assert normalized['content'] == 'hi my app is not working'
        assert normalized['channel_message_id'] == 'SM-TEST001'
    
    def test_normalized_format_correct(self, whatsapp_handler, sample_whatsapp):
        """Test normalized format has all required fields."""
        normalized = whatsapp_handler.normalize_message(sample_whatsapp)
        
        required_fields = [
            'channel', 'customer_email', 'customer_phone', 'customer_name',
            'subject', 'content', 'channel_message_id', 'received_at', 'metadata'
        ]
        
        for field in required_fields:
            assert field in normalized, f"Missing field: {field}"
    
    def test_send_message_saves_to_file(self, whatsapp_handler, tmp_path):
        """Test send_message saves to simulation file."""
        whatsapp_handler.simulation_dir = tmp_path
        
        result = whatsapp_handler.send_message(
            to_phone="+14155551234",
            body="Test WhatsApp message"
        )
        
        assert result['delivery_status'] == 'simulated'
        assert 'channel_message_id' in result
        
        # Check file was created
        sent_file = tmp_path / "whatsapp_sent.json"
        assert sent_file.exists()
        
        with open(sent_file, 'r') as f:
            sent_messages = json.load(f)
        
        assert len(sent_messages) == 1
        assert sent_messages[0]['to'] == '+14155551234'
    
    def test_format_response_under_300_chars(self, whatsapp_handler):
        """Test WhatsApp response is under 300 characters."""
        long_text = "a" * 500
        response = whatsapp_handler.format_response(long_text, {})
        
        assert len(response) <= whatsapp_handler.max_response_length + len(whatsapp_handler.human_prompt) + 5
    
    def test_format_response_has_human_prompt(self, whatsapp_handler):
        """Test WhatsApp response includes human prompt."""
        response = whatsapp_handler.format_response("Here's help.", {})
        
        assert "human" in response.lower()
    
    def test_long_messages_split_correctly(self, whatsapp_handler):
        """Test long messages are split into chunks."""
        long_text = "a" * 4000  # 4000 chars
        chunks = whatsapp_handler.format_for_whatsapp(long_text)
        
        assert len(chunks) > 1
        for chunk in chunks[:-1]:  # All but last should be near max
            assert len(chunk) <= whatsapp_handler.max_message_length
    
    def test_validate_webhook_valid(self, whatsapp_handler):
        """Test webhook validation accepts valid data."""
        valid = {
            "from": "whatsapp:+14155551234",
            "body": "test message"
        }
        assert whatsapp_handler.validate_incoming(valid) is True
    
    def test_validate_webhook_invalid(self, whatsapp_handler):
        """Test webhook validation rejects invalid data."""
        # Missing from
        assert whatsapp_handler.validate_incoming({"body": "test"}) is False
        
        # Missing body
        assert whatsapp_handler.validate_incoming({"from": "whatsapp:+123"}) is False
    
    def test_clean_phone_number(self, whatsapp_handler):
        """Test phone number cleaning."""
        # With whatsapp: prefix
        assert whatsapp_handler._clean_phone_number("whatsapp:+14155551234") == "+14155551234"
        
        # US 10 digit
        assert whatsapp_handler._clean_phone_number("4155551234") == "+14155551234"
        
        # Already formatted
        assert whatsapp_handler._clean_phone_number("+44207123456") == "+44207123456"


# ============================================================================
# TEST 3: Web Form Handler
# ============================================================================

class TestWebFormHandler:
    """Test Web Form handler functionality."""
    
    def test_valid_submission_accepted(self, web_form_handler, sample_web_form):
        """Test valid form submission is accepted."""
        submission = SupportFormSubmission(**sample_web_form)
        normalized = web_form_handler.process_submission(submission)
        
        assert normalized['channel'] == 'web_form'
        assert normalized['customer_email'] == 'test@example.com'
        assert normalized['customer_name'] == 'Test User'
    
    def test_invalid_email_rejected(self, web_form_handler):
        """Test invalid email is rejected."""
        with pytest.raises(ValueError):
            SupportFormSubmission(
                name="Test",
                email="invalid-email",
                subject="Test Subject Here",
                category="General",
                message="This is a test message with enough characters."
            )
    
    def test_short_message_rejected(self, web_form_handler):
        """Test short message is rejected."""
        with pytest.raises(ValueError):
            SupportFormSubmission(
                name="Test",
                email="test@example.com",
                subject="Test Subject Here",
                category="General",
                message="Short"  # Less than 10 chars
            )
    
    def test_invalid_category_rejected(self, web_form_handler):
        """Test invalid category is rejected."""
        with pytest.raises(ValueError):
            SupportFormSubmission(
                name="Test",
                email="test@example.com",
                subject="Test Subject Here",
                category="InvalidCategory",
                message="This is a test message with enough characters."
            )
    
    def test_response_has_semi_formal_tone(self, web_form_handler):
        """Test web form response has semi-formal tone."""
        response = web_form_handler.format_response(
            "We've received your request.",
            {"name": "John", "ticket_id": "TKT-123"}
        )
        
        assert "Hello" in response or "Dear" in response
        assert "Best regards" in response
        assert "TechCorp Support Team" in response
    
    def test_response_includes_ticket_reference(self, web_form_handler):
        """Test response includes ticket reference when available."""
        response = web_form_handler.format_response(
            "We're looking into it.",
            {"name": "John", "ticket_id": "TKT-123"}
        )
        
        assert "TKT-123" in response
    
    def test_validate_incoming_valid(self, web_form_handler, sample_web_form):
        """Test validation accepts valid form data."""
        assert web_form_handler.validate_incoming(sample_web_form) is True
    
    def test_validate_incoming_invalid(self, web_form_handler):
        """Test validation rejects invalid form data."""
        # Missing name
        assert web_form_handler.validate_incoming({
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message here"
        }) is False
        
        # Invalid email
        assert web_form_handler.validate_incoming({
            "name": "Test",
            "email": "invalid",
            "subject": "Test",
            "message": "Test message here"
        }) is False
        
        # Short message
        assert web_form_handler.validate_incoming({
            "name": "Test",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Short"
        }) is False


# ============================================================================
# TEST 4: Base Channel
# ============================================================================

class TestBaseChannel:
    """Test base channel functionality."""
    
    def test_normalize_message_abstractmethod(self):
        """Test that normalize_message must be implemented."""
        class TestHandler(BaseChannel):
            def format_response(self, response_text, customer_data):
                return response_text
            def validate_incoming(self, raw_data):
                return True
        
        # Python raises TypeError when trying to instantiate abstract class
        with pytest.raises(TypeError):
            TestHandler()
    
    def test_clean_text(self, gmail_handler):
        """Test text cleaning."""
        # Extra whitespace
        assert gmail_handler._clean_text("  hello   world  ") == "hello world"
        
        # Empty
        assert gmail_handler._clean_text("") == ""
        assert gmail_handler._clean_text(None) == ""
    
    def test_generate_message_id(self, gmail_handler):
        """Test message ID generation."""
        id1 = gmail_handler._generate_message_id("TEST")
        id2 = gmail_handler._generate_message_id("TEST")
        
        assert id1.startswith("TEST-")
        assert id2.startswith("TEST-")
        assert id1 != id2  # Should be unique
    
    def test_get_timestamp(self, gmail_handler):
        """Test timestamp generation."""
        timestamp = gmail_handler._get_timestamp()
        
        # Should be valid ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail("Invalid ISO timestamp format")
    
    def test_get_channel_metadata(self, gmail_handler):
        """Test channel metadata."""
        metadata = gmail_handler.get_channel_metadata()
        
        assert 'channel_name' in metadata
        assert 'class_name' in metadata
        assert metadata['channel_name'] == 'email'


# ============================================================================
# TEST 5: Cross Channel Format Test
# ============================================================================

class TestCrossChannelFormat:
    """Test that same message is formatted differently per channel."""
    
    def test_same_message_different_formats(self, gmail_handler, whatsapp_handler, web_form_handler):
        """Test same message formatted differently for each channel."""
        base_message = "We've received your request and are looking into the issue. We'll get back to you soon."
        customer_data = {"name": "John", "ticket_id": "TKT-123"}
        
        email_response = gmail_handler.format_response(base_message, customer_data)
        whatsapp_response = whatsapp_handler.format_response(base_message, customer_data)
        web_response = web_form_handler.format_response(base_message, customer_data)
        
        # Email: has greeting + signature, longer
        assert "Dear John," in email_response
        assert "Best regards," in email_response
        assert len(email_response) > 100
        
        # WhatsApp: short, no formal greeting, has human prompt
        assert "Dear" not in whatsapp_response
        assert "human" in whatsapp_response.lower()
        assert len(whatsapp_response) < 350
        
        # Web: semi-formal, has ticket reference
        assert "TKT-123" in web_response
        assert "Hello" in web_response or "Dear" in web_response
    
    def test_email_has_greeting_signature(self, gmail_handler):
        """Test email format has greeting and signature."""
        response = gmail_handler.format_response("Test", {"name": "John"})
        
        assert response.startswith("Dear John,")
        assert "Best regards," in response
        assert "TechCorp Support Team" in response
    
    def test_whatsapp_short_no_greeting(self, whatsapp_handler):
        """Test WhatsApp format is short with no formal greeting."""
        response = whatsapp_handler.format_response("Test response", {})
        
        assert not response.startswith("Dear")
        assert not response.startswith("Hello")
        assert len(response) <= 350
    
    def test_web_semi_formal_ticket_ref(self, web_form_handler):
        """Test web form format is semi-formal with ticket reference."""
        response = web_form_handler.format_response("Test", {"name": "John", "ticket_id": "TKT-456"})
        
        assert "TKT-456" in response
        assert "Best regards," in response


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
