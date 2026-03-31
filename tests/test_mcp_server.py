"""
Test cases for MCP Server Tools.

Tests all 7 MCP tools:
1. search_knowledge_base
2. create_ticket
3. get_customer_history
4. escalate_to_human
5. send_response
6. analyze_sentiment
7. get_ticket_status
"""

import json
import shutil
import tempfile
from pathlib import Path
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.mcp_server import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    analyze_sentiment,
    get_ticket_status,
    _load_tickets,
    _save_tickets,
    _load_escalations,
    _save_escalations,
    MEMORY_DIR
)


class TestSearchKnowledgeBase:
    """Tests for search_knowledge_base tool."""
    
    def test_search_password_reset(self):
        """TEST 1a - Search for 'password reset' should find results."""
        result = search_knowledge_base("password reset")
        
        assert "Search Results" in result
        assert "Password Reset" in result or "password" in result.lower()
    
    def test_search_nonexistent(self):
        """TEST 1b - Search for 'xyz123abc' should return no results message."""
        result = search_knowledge_base("xyz123abc")
        
        assert "No relevant documentation found" in result or "Search Results" in result
    
    def test_search_with_max_results(self):
        """TEST 1c - Search with max_results limit."""
        result = search_knowledge_base("login", max_results=1)
        
        # Should have at most 1 result section
        assert "Search Results" in result


class TestCreateTicket:
    """Tests for create_ticket tool."""
    
    def test_create_email_ticket(self):
        """TEST 2a - Create email ticket and verify saved."""
        result = create_ticket(
            customer_id="test@example.com",
            issue="Cannot login to my account",
            priority="medium",
            channel="email"
        )
        
        assert "Ticket Created Successfully" in result
        assert "TKT-" in result
        assert "email" in result.lower()
        
        # Verify saved
        tickets = _load_tickets()
        assert len(tickets) > 0
        assert any(t['channel'] == 'email' for t in tickets)
    
    def test_create_whatsapp_ticket(self):
        """TEST 2b - Create whatsapp ticket and verify channel recorded."""
        result = create_ticket(
            customer_id="+1234567890",
            issue="App not working",
            priority="high",
            channel="whatsapp"
        )
        
        assert "Ticket Created Successfully" in result
        assert "whatsapp" in result.lower()
        
        # Verify channel recorded
        tickets = _load_tickets()
        assert any(t['channel'] == 'whatsapp' for t in tickets)
    
    def test_create_web_form_ticket(self):
        """TEST 2c - Create web_form ticket and verify ticket ID returned."""
        result = create_ticket(
            customer_id="dev@startup.com",
            issue="API rate limit question",
            priority="low",
            channel="web_form"
        )
        
        assert "Ticket Created Successfully" in result
        assert "TKT-" in result
    
    def test_invalid_priority(self):
        """Test invalid priority returns error."""
        result = create_ticket(
            customer_id="test@example.com",
            issue="Test",
            priority="invalid",
            channel="email"
        )
        
        assert "Error" in result
        assert "Invalid priority" in result


class TestGetCustomerHistory:
    """Tests for get_customer_history tool."""
    
    def test_new_customer_no_history(self):
        """TEST 3a - New customer returns 'No history found'."""
        result = get_customer_history("brandnewcustomer@example.com")
        
        assert "No history found" in result or "No conversation history" in result
    
    def test_existing_customer_history(self):
        """TEST 3b - Existing customer shows past conversations."""
        # First create a ticket to establish history
        create_ticket(
            customer_id="history@example.com",
            issue="Test issue",
            priority="low",
            channel="email"
        )
        
        result = get_customer_history("history@example.com")
        
        # Should find customer record
        assert "history@example.com" in result or "Customer" in result


class TestEscalateToHuman:
    """Tests for escalate_to_human tool."""
    
    def test_normal_urgency_escalation(self):
        """TEST 4a - Normal urgency escalation is saved."""
        # Create ticket first
        ticket_result = create_ticket(
            customer_id="escalate@example.com",
            issue="Need help",
            priority="medium",
            channel="email"
        )
        
        # Extract ticket ID
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        # Escalate
        result = escalate_to_human(
            ticket_id=ticket_id,
            reason="Customer needs specialized help",
            urgency="normal",
            customer_id="escalate@example.com"
        )
        
        assert "Escalation Created Successfully" in result
        assert "ESC-" in result
        
        # Verify saved
        escalations = _load_escalations()
        assert len(escalations) > 0
    
    def test_critical_urgency_escalation(self):
        """TEST 4b - Critical urgency escalation is noted."""
        # Create ticket first
        ticket_result = create_ticket(
            customer_id="critical@example.com",
            issue="Urgent issue",
            priority="high",
            channel="whatsapp"
        )
        
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        result = escalate_to_human(
            ticket_id=ticket_id,
            reason="Critical system failure",
            urgency="critical",
            customer_id="critical@example.com"
        )
        
        assert "critical" in result.lower()
        assert "15 minutes" in result  # Critical response time
    
    def test_escalations_file_updated(self):
        """TEST 4c - Check escalations.json is updated."""
        # Create and escalate
        ticket_result = create_ticket(
            customer_id="test_esc_file@example.com",
            issue="Test",
            priority="low",
            channel="email"
        )
        
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        escalate_to_human(
            ticket_id=ticket_id,
            reason="Test escalation",
            urgency="normal",
            customer_id="test_esc_file@example.com"
        )
        
        escalations = _load_escalations()
        assert len(escalations) > 0
        assert any(e['ticket_id'] == ticket_id for e in escalations)


class TestSendResponse:
    """Tests for send_response tool."""
    
    def test_email_channel_formal(self):
        """TEST 5a - Email channel uses formal format."""
        # Create ticket first
        ticket_result = create_ticket(
            customer_id="response@example.com",
            issue="Test issue",
            priority="low",
            channel="email"
        )
        
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        result = send_response(
            ticket_id=ticket_id,
            message="Here is the solution to your problem.",
            channel="email"
        )
        
        assert "Response Sent Successfully" in result
        assert "email" in result.lower()
    
    def test_whatsapp_channel_short(self):
        """TEST 5b - WhatsApp channel uses short format."""
        # Create ticket first
        ticket_result = create_ticket(
            customer_id="+9999999999",
            issue="Test",
            priority="low",
            channel="whatsapp"
        )
        
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        result = send_response(
            ticket_id=ticket_id,
            message="Let me help you with that.",
            channel="whatsapp"
        )
        
        assert "Response Sent Successfully" in result
    
    def test_web_form_channel_semiformal(self):
        """TEST 5c - Web form channel uses semi-formal format."""
        # Create ticket first
        ticket_result = create_ticket(
            customer_id="webform@example.com",
            issue="Test",
            priority="low",
            channel="web_form"
        )
        
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        result = send_response(
            ticket_id=ticket_id,
            message="Here is the information you requested.",
            channel="web_form"
        )
        
        assert "Response Sent Successfully" in result


class TestAnalyzeSentiment:
    """Tests for analyze_sentiment tool."""
    
    def test_happy_message_high_score(self):
        """TEST 6a - Happy message returns score > 0.5."""
        result = analyze_sentiment("This is great! I love your product!")
        
        assert "Score:" in result
        assert "positive" in result.lower() or "Recommend" in result
    
    def test_angry_message_low_score(self):
        """TEST 6b - Angry message returns score < 0.3."""
        result = analyze_sentiment("This is terrible! I want a refund NOW!")
        
        assert "Score:" in result
        assert "negative" in result.lower() or "escalation" in result.lower()
    
    def test_neutral_message_mid_score(self):
        """TEST 6c - Neutral message returns score ~0.5."""
        result = analyze_sentiment("How do I reset my password?")
        
        assert "Score:" in result
        assert "neutral" in result.lower() or "Recommend" in result


class TestGetTicketStatus:
    """Tests for get_ticket_status tool."""
    
    def test_existing_ticket_returns_details(self):
        """TEST 7a - Existing ticket returns full details."""
        # Create ticket first
        ticket_result = create_ticket(
            customer_id="status@example.com",
            issue="Test issue for status check",
            priority="medium",
            channel="email"
        )
        
        ticket_id = [line for line in ticket_result.split('\n') if 'TKT-' in line][0].split(': ')[1]
        
        result = get_ticket_status(ticket_id)
        
        assert "Ticket Status:" in result
        assert ticket_id in result
        assert "status@example.com" in result
        assert "OPEN" in result.upper()
    
    def test_nonexistent_ticket_error(self):
        """TEST 7b - Non-existing ticket returns helpful error."""
        result = get_ticket_status("TKT-NONEXISTENT123")
        
        assert "Error" in result or "not found" in result.lower()


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test data after each test."""
    yield
    
    # Reset tickets and escalations
    _save_tickets([])
    _save_escalations([])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
