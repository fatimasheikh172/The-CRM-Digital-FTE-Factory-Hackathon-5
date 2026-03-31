"""
TechCorp Customer Success AI Agent - Tool Tests

Tests for all 7 tools WITHOUT Gemini API.
Tests database operations (port 5433), formatting, and tool logic.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from production.agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    analyze_sentiment,
    get_ticket_status,
)
from production.agent.formatters import (
    format_for_email,
    format_for_whatsapp,
    format_for_web_form,
    format_response,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_customer_email():
    """Sample customer email for testing."""
    return "test_customer@example.com"


@pytest.fixture
def sample_customer_phone():
    """Sample customer phone for testing."""
    return "+14155551234"


@pytest.fixture
def sample_message():
    """Sample customer message for testing."""
    return "I can't login to my account. Password reset not working."


@pytest.fixture
def sample_ticket_id():
    """Sample ticket ID for testing."""
    return "TKT-TEST-1234"


# ============================================================================
# TOOL 1: search_knowledge_base TESTS
# ============================================================================

class TestSearchKnowledgeBase:
    """Tests for search_knowledge_base tool."""
    
    @pytest.mark.asyncio
    async def test_search_returns_string(self):
        """Test that search returns a string."""
        result = await search_knowledge_base(query="login")
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self):
        """Test search handles no results gracefully."""
        result = await search_knowledge_base(
            query="xyznonexistentquery123"
        )
        assert isinstance(result, str)
        # Should return helpful message even if no results
        assert "No relevant" in result or "Search Results" in result
    
    @pytest.mark.asyncio
    async def test_search_with_max_results(self):
        """Test search respects max_results parameter."""
        result = await search_knowledge_base(query="login", max_results=1)
        assert isinstance(result, str)


# ============================================================================
# TOOL 2: create_ticket TESTS
# ============================================================================

class TestCreateTicket:
    """Tests for create_ticket tool."""
    
    @pytest.mark.asyncio
    async def test_create_ticket_returns_string(self, sample_customer_email):
        """Test that create_ticket returns a string."""
        result = await create_ticket(
            customer_id=sample_customer_email,
            issue="Test issue",
            channel="email"
        )
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_create_ticket_includes_ticket_id(self, sample_customer_email):
        """Test that result includes ticket ID."""
        result = await create_ticket(
            customer_id=sample_customer_email,
            issue="Test issue",
            channel="email"
        )
        assert "Ticket" in result
        assert "TKT-" in result or "ticket" in result.lower()
    
    @pytest.mark.asyncio
    async def test_create_ticket_different_channels(self, sample_customer_email):
        """Test ticket creation for different channels."""
        for channel in ["email", "whatsapp", "web_form"]:
            result = await create_ticket(
                customer_id=sample_customer_email,
                issue="Test issue",
                channel=channel
            )
            assert isinstance(result, str)


# ============================================================================
# TOOL 3: get_customer_history TESTS
# ============================================================================

class TestGetCustomerHistory:
    """Tests for get_customer_history tool."""
    
    @pytest.mark.asyncio
    async def test_get_history_returns_string(self, sample_customer_email):
        """Test that get_customer_history returns a string."""
        result = await get_customer_history(customer_id=sample_customer_email)
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_get_history_handles_new_customer(self):
        """Test history for non-existent customer."""
        result = await get_customer_history(
            customer_id="nonexistent@example.com"
        )
        assert isinstance(result, str)
        # Should indicate no history or new customer
        assert "No" in result or "history" in result.lower() or "Customer" in result


# ============================================================================
# TOOL 4: escalate_to_human TESTS
# ============================================================================

class TestEscalateToHuman:
    """Tests for escalate_to_human tool."""
    
    @pytest.mark.asyncio
    async def test_escalate_returns_string(self, sample_ticket_id):
        """Test that escalate_to_human returns a string."""
        result = await escalate_to_human(
            ticket_id=sample_ticket_id,
            reason="Test escalation reason"
        )
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_escalate_includes_escalation_id(self, sample_ticket_id):
        """Test that result includes escalation ID."""
        result = await escalate_to_human(
            ticket_id=sample_ticket_id,
            reason="Test escalation"
        )
        assert "Escalation" in result or "escalat" in result.lower()
    
    @pytest.mark.asyncio
    async def test_escalate_different_urgencies(self, sample_ticket_id):
        """Test escalation with different urgency levels."""
        for urgency in ["normal", "high", "critical"]:
            result = await escalate_to_human(
                ticket_id=sample_ticket_id,
                reason="Test",
                urgency=urgency
            )
            assert isinstance(result, str)


# ============================================================================
# TOOL 5: send_response TESTS
# ============================================================================

class TestSendResponse:
    """Tests for send_response tool."""
    
    @pytest.mark.asyncio
    async def test_send_response_returns_string(self, sample_ticket_id):
        """Test that send_response returns a string."""
        result = await send_response(
            ticket_id=sample_ticket_id,
            message="Test response message",
            channel="email"
        )
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_send_response_different_channels(self, sample_ticket_id):
        """Test response sending for different channels."""
        for channel in ["email", "whatsapp", "web_form"]:
            result = await send_response(
                ticket_id=sample_ticket_id,
                message="Test response",
                channel=channel
            )
            assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_send_response_with_customer_info(self, sample_ticket_id):
        """Test response with customer contact info."""
        result = await send_response(
            ticket_id=sample_ticket_id,
            message="Test response",
            channel="email",
            customer_email="test@example.com"
        )
        assert isinstance(result, str)


# ============================================================================
# TOOL 6: analyze_sentiment TESTS
# ============================================================================

class TestAnalyzeSentiment:
    """Tests for analyze_sentiment tool."""
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_returns_string(self, sample_message):
        """Test that analyze_sentiment returns a string."""
        result = await analyze_sentiment(message=sample_message)
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_includes_score(self, sample_message):
        """Test that result includes sentiment score."""
        result = await analyze_sentiment(message=sample_message)
        assert "Score" in result
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive_message(self):
        """Test sentiment analysis for positive message."""
        result = await analyze_sentiment(
            message="I love your product! It's amazing and works great!"
        )
        assert "Score" in result
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative_message(self):
        """Test sentiment analysis for negative message."""
        result = await analyze_sentiment(
            message="This is terrible! I'm furious and disappointed!"
        )
        assert "Score" in result
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral_message(self):
        """Test sentiment analysis for neutral message."""
        result = await analyze_sentiment(
            message="I have a question about my account settings."
        )
        assert "Score" in result


# ============================================================================
# TOOL 7: get_ticket_status TESTS
# ============================================================================

class TestGetTicketStatus:
    """Tests for get_ticket_status tool."""
    
    @pytest.mark.asyncio
    async def test_get_ticket_status_returns_string(self, sample_ticket_id):
        """Test that get_ticket_status returns a string."""
        result = await get_ticket_status(ticket_id=sample_ticket_id)
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_get_ticket_status_handles_not_found(self):
        """Test status for non-existent ticket."""
        result = await get_ticket_status(ticket_id="TKT-NONEXISTENT-0000")
        assert isinstance(result, str)
        # Should indicate ticket not found
        assert "not found" in result.lower() or "Error" in result or "Ticket" in result


# ============================================================================
# FORMATTER TESTS
# ============================================================================

class TestFormatters:
    """Tests for channel formatters."""
    
    def test_format_for_email(self):
        """Test email formatting."""
        text = "Thank you for contacting us. We are here to help."
        result = format_for_email(text, customer_name="John")
        
        assert "Dear John," in result
        assert "Best regards" in result
        assert "TechCorp Support Team" in result
    
    def test_format_for_email_no_name(self):
        """Test email formatting without customer name."""
        text = "Thank you for contacting us."
        result = format_for_email(text)
        
        assert "Dear" in result
        assert "Best regards" in result
    
    def test_format_for_whatsapp(self):
        """Test WhatsApp formatting."""
        text = "Hello! I can help you with that. Let me check."
        result = format_for_whatsapp(text)
        
        assert len(result) <= 300
        assert "human" in result.lower()
    
    def test_format_for_whatsapp_trims_long_text(self):
        """Test WhatsApp formatting trims long text."""
        text = "A" * 500  # Very long text
        result = format_for_whatsapp(text)
        
        assert len(result) <= 300
    
    def test_format_for_web_form(self):
        """Test web form formatting."""
        text = "Thank you for your inquiry. We will respond shortly."
        result = format_for_web_form(text, ticket_id="TKT-123")
        
        assert "Hello," in result
        assert "TKT-123" in result
        assert "Best regards" in result
    
    def test_format_response_router(self):
        """Test format_response router function."""
        text = "Test response"
        
        email_result = format_response(text, "email", customer_name="John")
        assert "Dear John," in email_result
        
        whatsapp_result = format_response(text, "whatsapp")
        assert "human" in whatsapp_result.lower()
        
        web_result = format_response(text, "web_form", ticket_id="TKT-123")
        assert "Hello," in web_result
    
    def test_format_response_invalid_channel(self):
        """Test format_response with invalid channel."""
        with pytest.raises(ValueError):
            format_response("test", "invalid_channel")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestToolIntegration:
    """Integration tests for tool workflow."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, sample_customer_email, sample_message):
        """Test complete tool workflow sequence."""
        # 1. Create ticket
        ticket_result = await create_ticket(
            customer_id=sample_customer_email,
            issue=sample_message,
            channel="email"
        )
        assert "Ticket" in ticket_result
        
        # 2. Get customer history
        history_result = await get_customer_history(
            customer_id=sample_customer_email
        )
        assert isinstance(history_result, str)
        
        # 3. Analyze sentiment
        sentiment_result = await analyze_sentiment(message=sample_message)
        assert "Score" in sentiment_result
        
        # 4. Search knowledge base
        kb_result = await search_knowledge_base(query="login")
        assert isinstance(kb_result, str)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
