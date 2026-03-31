"""
Integration Tests for MCP Server.

Tests complete customer journeys using MCP tools:
1. Happy Path (Email) - Full resolution flow
2. Escalation Path (WhatsApp) - Refund escalation flow
3. Cross Channel Journey - Multi-channel support flow
"""

import json
import sys
from pathlib import Path

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
    _save_escalations
)


def cleanup_data():
    """Reset tickets and escalations."""
    _save_tickets([])
    _save_escalations([])


def extract_ticket_id(result: str) -> str:
    """Extract ticket ID from create_ticket result."""
    for line in result.split('\n'):
        if 'TKT-' in line:
            return line.split(': ')[1].strip()
    return None


class TestJourney1HappyPathEmail:
    """
    JOURNEY 1 - Happy Path (Email)
    
    Customer contacts via email with login issue.
    Agent resolves the issue successfully.
    """
    
    def test_full_resolution_flow(self):
        """Test complete happy path from contact to resolution."""
        cleanup_data()
        
        # Step 1: analyze_sentiment("I need help with login")
        sentiment_result = analyze_sentiment("I need help with login")
        assert "Score:" in sentiment_result
        
        # Step 2: create_ticket(customer, issue, medium, email)
        ticket_result = create_ticket(
            customer_id="happy@example.com",
            issue="I need help with login",
            priority="medium",
            channel="email"
        )
        assert "Ticket Created Successfully" in ticket_result
        ticket_id = extract_ticket_id(ticket_result)
        assert ticket_id is not None
        
        # Step 3: get_customer_history(customer_id)
        history_result = get_customer_history("happy@example.com")
        assert "happy@example.com" in history_result or "Customer" in history_result
        
        # Step 4: search_knowledge_base("login help")
        search_result = search_knowledge_base("login help")
        assert "Search Results" in search_result
        
        # Step 5: send_response(ticket_id, response, email)
        response_result = send_response(
            ticket_id=ticket_id,
            message="Dear Customer,\n\nI understand you're having trouble logging in. Please try resetting your password by clicking 'Forgot Password' on the login page.\n\nBest regards,\nTechCorp Support",
            channel="email"
        )
        assert "Response Sent Successfully" in response_result
        
        # Step 6: get_ticket_status(ticket_id)
        status_result = get_ticket_status(ticket_id)
        assert ticket_id in status_result
        assert "happy@example.com" in status_result
        
        # Verify: Ticket should exist and have messages
        tickets = _load_tickets()
        ticket = next((t for t in tickets if t['ticket_id'] == ticket_id), None)
        assert ticket is not None
        assert len(ticket.get('messages', [])) > 0
        
        cleanup_data()


class TestJourney2EscalationPathWhatsApp:
    """
    JOURNEY 2 - Escalation Path (WhatsApp)
    
    Customer contacts via WhatsApp demanding refund.
    Agent detects critical sentiment and escalates.
    """
    
    def test_refund_escalation_flow(self):
        """Test escalation flow for angry refund request."""
        cleanup_data()
        
        # Step 1: analyze_sentiment("I WANT A REFUND NOW")
        sentiment_result = analyze_sentiment("I WANT A REFUND NOW")
        assert "Score:" in sentiment_result
        # Should detect negative sentiment
        
        # Step 2: create_ticket(customer, issue, high, whatsapp)
        ticket_result = create_ticket(
            customer_id="+1555123456",
            issue="I WANT A REFUND NOW",
            priority="high",
            channel="whatsapp"
        )
        assert "Ticket Created Successfully" in ticket_result
        ticket_id = extract_ticket_id(ticket_result)
        assert ticket_id is not None
        
        # Step 3: analyze_sentiment → should show critical
        sentiment_result2 = analyze_sentiment("This is unacceptable! I want my money back!")
        assert "Score:" in sentiment_result2
        # Should show negative sentiment with escalation recommendation
        
        # Step 4: escalate_to_human(ticket_id, refund, critical)
        escalation_result = escalate_to_human(
            ticket_id=ticket_id,
            reason="Customer demanding refund - very angry",
            urgency="critical",
            customer_id="+1555123456"
        )
        assert "Escalation Created Successfully" in escalation_result
        assert "ESC-" in escalation_result
        assert "critical" in escalation_result.lower()
        
        # Step 5: get_ticket_status(ticket_id)
        status_result = get_ticket_status(ticket_id)
        assert ticket_id in status_result
        assert "ESCALATED" in status_result.upper()
        
        # Verify: Ticket status should be escalated
        tickets = _load_tickets()
        ticket = next((t for t in tickets if t['ticket_id'] == ticket_id), None)
        assert ticket is not None
        assert ticket['status'] == 'escalated'
        assert ticket.get('escalation') is not None
        
        # Verify: Escalation should be saved
        escalations = _load_escalations()
        assert len(escalations) > 0
        assert any(e['urgency'] == 'critical' for e in escalations)
        
        cleanup_data()


class TestJourney3CrossChannel:
    """
    JOURNEY 3 - Cross Channel Journey
    
    Customer contacts via email first.
    Then contacts via WhatsApp about same issue.
    Agent recognizes customer and references email history.
    """
    
    def test_multi_channel_support_flow(self):
        """Test cross-channel recognition and context."""
        cleanup_data()
        
        customer_email = "crosschannel@example.com"
        customer_phone = "+1555987654"
        
        # Step 1: create_ticket(customer_A, email issue, email)
        ticket1_result = create_ticket(
            customer_id=customer_email,
            issue="Cannot access my dashboard",
            priority="medium",
            channel="email"
        )
        assert "Ticket Created Successfully" in ticket1_result
        ticket_id1 = extract_ticket_id(ticket1_result)
        
        # Step 2: send_response via email
        response1_result = send_response(
            ticket_id=ticket_id1,
            message="Dear Customer,\n\nI understand you're having trouble accessing your dashboard. Let me help you troubleshoot this issue.\n\nBest regards,\nTechCorp Support",
            channel="email"
        )
        assert "Response Sent Successfully" in response1_result
        
        # Step 3: Same customer contacts via whatsapp
        # (In real scenario, would use phone lookup to find email)
        ticket2_result = create_ticket(
            customer_id=customer_phone,
            issue="Still can't access dashboard - following up on email",
            priority="high",
            channel="whatsapp"
        )
        assert "Ticket Created Successfully" in ticket2_result
        ticket_id2 = extract_ticket_id(ticket2_result)
        
        # Step 4: get_customer_history → should show email history
        # Check email customer history
        history_email = get_customer_history(customer_email)
        assert customer_email in history_email or "Customer" in history_email
        
        # Step 5: send_response via whatsapp with context
        response2_result = send_response(
            ticket_id=ticket_id2,
            message="I see you contacted us via email about this. Let me continue helping you here on WhatsApp.",
            channel="whatsapp"
        )
        assert "Response Sent Successfully" in response2_result
        
        # Verify: Both tickets should exist
        tickets = _load_tickets()
        assert len(tickets) >= 2
        
        # Verify: Email ticket has email channel
        email_ticket = next((t for t in tickets if t['ticket_id'] == ticket_id1), None)
        assert email_ticket is not None
        assert email_ticket['channel'] == 'email'
        
        # Verify: WhatsApp ticket has whatsapp channel
        whatsapp_ticket = next((t for t in tickets if t['ticket_id'] == ticket_id2), None)
        assert whatsapp_ticket is not None
        assert whatsapp_ticket['channel'] == 'whatsapp'
        
        # Verify: Both have messages
        assert len(email_ticket.get('messages', [])) > 0
        assert len(whatsapp_ticket.get('messages', [])) > 0
        
        cleanup_data()


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
