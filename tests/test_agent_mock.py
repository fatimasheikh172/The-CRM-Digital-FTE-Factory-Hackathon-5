"""
TechCorp Customer Success AI Agent - Mock Agent Tests

Tests for agent structure with mocked Gemini.
Tests agent initialization, tool definitions, and formatters.
No real API calls.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from production.agent.customer_success_agent import (
    CustomerSuccessAgent,
    process_message,
    TOOL_FUNCTIONS
)
from production.agent.formatters import (
    format_for_email,
    format_for_whatsapp,
    format_for_web_form,
    format_response,
    get_channel_limits
)
from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.config import AgentConfig


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
    return "I can't login to my account."


@pytest.fixture
def mock_mode_agent():
    """Create agent in mock mode."""
    return CustomerSuccessAgent(mock_mode=True)


# ============================================================================
# AGENT INITIALIZATION TESTS
# ============================================================================

class TestAgentInitialization:
    """Tests for CustomerSuccessAgent initialization."""
    
    def test_agent_creates_in_mock_mode(self):
        """Test agent creates successfully in mock mode."""
        agent = CustomerSuccessAgent(mock_mode=True)
        assert agent is not None
        assert agent.mock_mode is True
        assert agent.model is None
    
    def test_agent_creates_without_api_key(self):
        """Test agent creates without API key."""
        # Temporarily clear API key
        original_key = AgentConfig.GEMINI_API_KEY
        AgentConfig.GEMINI_API_KEY = ""
        
        try:
            agent = CustomerSuccessAgent()
            assert agent is not None
            assert agent.mock_mode is True
        finally:
            AgentConfig.GEMINI_API_KEY = original_key
    
    def test_agent_has_tool_functions(self):
        """Test that agent has access to all tool functions."""
        expected_tools = [
            "search_knowledge_base",
            "create_ticket",
            "get_customer_history",
            "escalate_to_human",
            "send_response",
            "analyze_sentiment",
            "get_ticket_status"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in TOOL_FUNCTIONS


# ============================================================================
# AGENT RUN TESTS (MOCK MODE)
# ============================================================================

class TestAgentRunMock:
    """Tests for agent run method in mock mode."""
    
    @pytest.mark.asyncio
    async def test_agent_run_returns_dict(self, mock_mode_agent, sample_message):
        """Test that agent.run returns a dictionary."""
        result = await mock_mode_agent.run(
            message=sample_message,
            channel="email",
            customer_id="test@example.com"
        )
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_agent_run_has_required_keys(self, mock_mode_agent, sample_message):
        """Test that result has all required keys."""
        result = await mock_mode_agent.run(
            message=sample_message,
            channel="email",
            customer_id="test@example.com"
        )
        
        required_keys = [
            "output",
            "tool_calls",
            "escalated",
            "escalation_reason",
            "channel",
            "processing_time_ms"
        ]
        
        for key in required_keys:
            assert key in result
    
    @pytest.mark.asyncio
    async def test_agent_run_different_channels(self, mock_mode_agent, sample_message):
        """Test agent run with different channels."""
        for channel in ["email", "whatsapp", "web_form"]:
            result = await mock_mode_agent.run(
                message=sample_message,
                channel=channel,
                customer_id="test@example.com"
            )
            assert result["channel"] == channel
    
    @pytest.mark.asyncio
    async def test_agent_run_logs_tool_calls(self, mock_mode_agent, sample_message):
        """Test that agent logs tool calls."""
        result = await mock_mode_agent.run(
            message=sample_message,
            channel="email",
            customer_id="test@example.com"
        )
        
        assert "tool_calls" in result
        assert isinstance(result["tool_calls"], list)
        assert len(result["tool_calls"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_run_has_processing_time(self, mock_mode_agent, sample_message):
        """Test that result includes processing time."""
        result = await mock_mode_agent.run(
            message=sample_message,
            channel="email",
            customer_id="test@example.com"
        )
        
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], int)
        assert result["processing_time_ms"] >= 0


# ============================================================================
# ESCALATION TESTS
# ============================================================================

class TestEscalationDetection:
    """Tests for escalation detection."""
    
    @pytest.mark.asyncio
    async def test_agent_detects_legal_keywords(self, mock_mode_agent):
        """Test agent detects legal threat keywords."""
        result = await mock_mode_agent.run(
            message="I'm going to call my lawyer and sue you!",
            channel="email",
            customer_id="angry@example.com"
        )
        
        assert result["escalated"] is True
    
    @pytest.mark.asyncio
    async def test_agent_detects_refund_request(self, mock_mode_agent):
        """Test agent detects refund request."""
        result = await mock_mode_agent.run(
            message="I want a refund and money back!",
            channel="email",
            customer_id="refund@example.com"
        )
        
        assert result["escalated"] is True
    
    @pytest.mark.asyncio
    async def test_agent_detects_human_request(self, mock_mode_agent):
        """Test agent detects human agent request."""
        result = await mock_mode_agent.run(
            message="I need to speak to a human agent now!",
            channel="email",
            customer_id="human@example.com"
        )
        
        assert result["escalated"] is True
    
    @pytest.mark.asyncio
    async def test_normal_query_not_escalated(self, mock_mode_agent):
        """Test that normal queries are not escalated."""
        result = await mock_mode_agent.run(
            message="How do I reset my password?",
            channel="email",
            customer_id="normal@example.com"
        )
        
        # Normal queries should not be escalated
        assert result["escalated"] is False


# ============================================================================
# PROCESS_MESSAGE CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestProcessMessage:
    """Tests for process_message convenience function."""
    
    @pytest.mark.asyncio
    async def test_process_message_returns_dict(self, sample_message):
        """Test that process_message returns a dictionary."""
        result = await process_message(
            message=sample_message,
            channel="email",
            customer_id="test@example.com",
            mock_mode=True
        )
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_process_message_with_email(self, sample_message):
        """Test process_message with email customer."""
        result = await process_message(
            message=sample_message,
            channel="email",
            customer_id="test@example.com",
            customer_email="test@example.com",
            mock_mode=True
        )
        assert "output" in result
    
    @pytest.mark.asyncio
    async def test_process_message_with_phone(self, sample_message):
        """Test process_message with phone customer."""
        result = await process_message(
            message=sample_message,
            channel="whatsapp",
            customer_id="+14155551234",
            customer_phone="+14155551234",
            mock_mode=True
        )
        assert "output" in result


# ============================================================================
# PROMPT TESTS
# ============================================================================

class TestPrompts:
    """Tests for system prompts."""
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert CUSTOMER_SUCCESS_SYSTEM_PROMPT is not None
        assert len(CUSTOMER_SUCCESS_SYSTEM_PROMPT) > 0
    
    def test_system_prompt_contains_workflow(self):
        """Test that prompt contains required workflow."""
        assert "create_ticket" in CUSTOMER_SUCCESS_SYSTEM_PROMPT
        assert "send_response" in CUSTOMER_SUCCESS_SYSTEM_PROMPT
    
    def test_system_prompt_contains_constraints(self):
        """Test that prompt contains hard constraints."""
        assert "NEVER" in CUSTOMER_SUCCESS_SYSTEM_PROMPT
        assert "ALWAYS" in CUSTOMER_SUCCESS_SYSTEM_PROMPT
    
    def test_system_prompt_contains_escalation_triggers(self):
        """Test that prompt contains escalation triggers."""
        assert "lawyer" in CUSTOMER_SUCCESS_SYSTEM_PROMPT
        assert "refund" in CUSTOMER_SUCCESS_SYSTEM_PROMPT


# ============================================================================
# CHANNEL LIMITS TESTS
# ============================================================================

class TestChannelLimits:
    """Tests for channel limit configuration."""
    
    def test_get_channel_limits_email(self):
        """Test channel limits for email."""
        limits = get_channel_limits("email")
        
        assert limits["type"] == "words"
        assert limits["limit"] == 500
        assert limits["requires_greeting"] is True
        assert limits["requires_signature"] is True
    
    def test_get_channel_limits_whatsapp(self):
        """Test channel limits for WhatsApp."""
        limits = get_channel_limits("whatsapp")
        
        assert limits["type"] == "characters"
        assert limits["limit"] == 300
        assert limits["requires_greeting"] is False
        assert "human_prompt" in limits
    
    def test_get_channel_limits_web_form(self):
        """Test channel limits for web form."""
        limits = get_channel_limits("web_form")
        
        assert limits["type"] == "words"
        assert limits["limit"] == 300
        assert limits["requires_greeting"] is True
    
    def test_get_channel_limits_invalid(self):
        """Test channel limits with invalid channel."""
        with pytest.raises(ValueError):
            get_channel_limits("invalid_channel")


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestConfig:
    """Tests for configuration."""
    
    def test_config_has_gemini_key(self):
        """Test config has Gemini API key field."""
        assert hasattr(AgentConfig, "GEMINI_API_KEY")
    
    def test_config_has_model(self):
        """Test config has model field."""
        assert hasattr(AgentConfig, "MODEL")
        assert AgentConfig.MODEL == "gemini-1.5-flash"
    
    def test_config_has_database_settings(self):
        """Test config has database settings."""
        assert hasattr(AgentConfig, "DB_HOST")
        assert hasattr(AgentConfig, "DB_PORT")
        assert AgentConfig.DB_PORT == 5433
    
    def test_config_has_channels(self):
        """Test config has channels list."""
        assert hasattr(AgentConfig, "CHANNELS")
        assert "email" in AgentConfig.CHANNELS
        assert "whatsapp" in AgentConfig.CHANNELS
        assert "web_form" in AgentConfig.CHANNELS
    
    def test_config_has_escalation_triggers(self):
        """Test config has escalation triggers."""
        assert hasattr(AgentConfig, "ESCALATION_TRIGGERS")
        assert "lawyer" in AgentConfig.ESCALATION_TRIGGERS
        assert "refund" in AgentConfig.ESCALATION_TRIGGERS


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
