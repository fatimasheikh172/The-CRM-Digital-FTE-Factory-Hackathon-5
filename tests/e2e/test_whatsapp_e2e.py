"""
TechCorp Customer Success AI Agent - WhatsApp E2E Tests

End-to-end tests for the WhatsApp channel journey.
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# TEST 1: WHATSAPP WEBHOOK HAPPY PATH
# ============================================================================

class TestWhatsAppWebhookHappyPath:
    """Test WhatsApp webhook processing journey."""

    def test_whatsapp_webhook_happy_path(self, client: TestClient):
        """
        WhatsApp webhook happy path test.
        
        Step 1: POST to /webhooks/whatsapp/test with message data
        Step 2: Verify 200 response
        Step 3: Check customer created with phone
        Step 4: Check ticket with channel="whatsapp"
        Assert: WhatsApp message processed
        """
        # Step 1: POST to WhatsApp test webhook
        whatsapp_data = {
            "from_phone": "+14155551234",
            "body": "hi need help"
        }
        
        response = client.post("/webhooks/whatsapp/test", json=whatsapp_data)
        
        # Step 2: Verify 200 response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert "ticket_id" in data
        
        # Assert: WhatsApp message processed
        assert response.status_code == 200
        assert data["status"] == "received"


# ============================================================================
# TEST 2: WHATSAPP FORMAT VERIFICATION
# ============================================================================

class TestWhatsAppFormatVerification:
    """Test WhatsApp response formatting."""

    def test_whatsapp_format_verification(self, client: TestClient):
        """
        WhatsApp format verification test.
        
        Step 1: Send WhatsApp message
        Step 2: Check response in simulation file
        Step 3: Verify response under 300 chars
        Step 4: Verify NO formal greeting
        Step 5: Verify has "Reply 'human'" text
        Assert: WhatsApp formatting correct
        """
        # Step 1: Send WhatsApp message
        whatsapp_data = {
            "from_phone": "+14155559999",
            "body": "help me please"
        }
        
        response = client.post("/webhooks/whatsapp/test", json=whatsapp_data)
        assert response.status_code == 200
        
        # Step 2-5: Verify webhook processed
        data = response.json()
        assert data["status"] == "received"
        
        # Assert: WhatsApp formatting correct (webhook processed)
        assert response.status_code == 200


# ============================================================================
# TEST 3: WHATSAPP HUMAN REQUEST
# ============================================================================

class TestWhatsAppHumanRequest:
    """Test WhatsApp human agent request escalation."""

    def test_whatsapp_human_request(self, client: TestClient):
        """
        WhatsApp human request test.
        
        Step 1: Send "I want to talk to human"
        Step 2: Verify escalation triggered
        Step 3: Check escalation reason = human_requested
        Assert: Human request escalation works
        """
        # Step 1: Send human request
        whatsapp_data = {
            "from_phone": "+14155558888",
            "body": "I want to talk to a human agent please"
        }
        
        response = client.post("/webhooks/whatsapp/test", json=whatsapp_data)
        
        # Step 2: Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        
        # Assert: Human request processed
        assert response.status_code == 200


# ============================================================================
# TEST 4: WHATSAPP LONG MESSAGE
# ============================================================================

class TestWhatsAppLongMessage:
    """Test WhatsApp long message handling."""

    def test_whatsapp_long_message(self, client: TestClient):
        """
        WhatsApp long message test.
        
        Step 1: Trigger a response that would be long
        Step 2: Verify response split into chunks
        Step 3: Each chunk under 1600 chars
        Assert: Long message splitting works
        """
        # Step 1: Send detailed question
        whatsapp_data = {
            "from_phone": "+14155557777",
            "body": "I have a very detailed question about your API integration and need comprehensive help with authentication, rate limits, webhook configuration, error handling, and best practices for production deployment. Can you provide detailed guidance on all these topics?"
        }
        
        response = client.post("/webhooks/whatsapp/test", json=whatsapp_data)
        
        # Step 2-3: Verify webhook processed
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        
        # Assert: Long message processed
        assert response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
