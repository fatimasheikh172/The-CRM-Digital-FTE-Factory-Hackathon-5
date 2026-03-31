"""
Webhook Router for TechCorp Customer Success AI Agent.

Handles incoming webhooks from:
- Gmail (Pub/Sub notifications)
- WhatsApp (Twilio webhooks)
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Request, Form
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr

from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from kafka_client import FTEKafkaProducer, TOPICS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize handlers
gmail_handler = GmailHandler(simulation_mode=True)
whatsapp_handler = WhatsAppHandler(simulation_mode=True)

# Kafka producer (initialized per-request for simplicity)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class GmailTestSubmission(BaseModel):
    """Test Gmail submission model."""
    from_email: str
    subject: str
    body: str
    name: str = None


class WhatsAppTestSubmission(BaseModel):
    """Test WhatsApp submission model."""
    from_phone: str
    body: str


class WebhookResponse(BaseModel):
    """Generic webhook response."""
    status: str
    message: str = None
    ticket_id: str = None
    count: int = None


# ============================================================================
# GMAIL WEBHOOKS
# ============================================================================

@router.post("/gmail", response_model=WebhookResponse, tags=["Gmail"])
async def gmail_webhook(request: Request):
    """
    Receive Gmail Pub/Sub push notifications.
    
    In simulation mode, processes sample email data.
    In production, would receive actual Pub/Sub messages.
    
    Returns:
        Status confirmation with message count.
    """
    try:
        # Get request body
        body = await request.json()
        
        # Process email via GmailHandler
        if gmail_handler.simulation_mode:
            # Get sample email
            emails = [gmail_handler._get_sample_email()]
        else:
            # Parse Pub/Sub notification
            emails = gmail_handler.parse_pubsub_notification(body)
        
        # Publish each email to Kafka
        producer = FTEKafkaProducer()
        await producer.start()
        
        count = 0
        for email in emails:
            normalized = gmail_handler.normalize_message(email)
            await producer.publish(TOPICS["tickets_incoming"], normalized)
            count += 1
        
        await producer.stop()
        
        logger.info(f"Processed {count} Gmail messages")
        
        return WebhookResponse(
            status="received",
            message=f"Processed {count} email(s)",
            count=count
        )
        
    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Gmail webhook: {str(e)}"
        )


@router.post("/gmail/test", response_model=WebhookResponse, tags=["Gmail"])
async def gmail_test(submission: GmailTestSubmission):
    """
    Test endpoint for Gmail simulation.
    
    Accepts test email data and publishes to Kafka.
    
    Args:
        submission: Test email data with from, subject, body.
        
    Returns:
        Ticket confirmation.
    """
    try:
        # Create email data
        email_data = {
            "from": f"{submission.name or 'Test User'} <{submission.from_email}>",
            "subject": submission.subject,
            "body": submission.body,
            "message_id": gmail_handler._generate_message_id("TEST"),
            "received_at": gmail_handler._get_timestamp()
        }
        
        # Normalize
        normalized = gmail_handler.normalize_message(email_data)
        
        # Publish to Kafka
        producer = FTEKafkaProducer()
        await producer.start()
        
        await producer.publish(TOPICS["tickets_incoming"], normalized)
        
        await producer.stop()
        
        logger.info(f"Test Gmail message published: {submission.subject}")
        
        return WebhookResponse(
            status="received",
            message="Test email published to Kafka",
            ticket_id=normalized.get("channel_message_id")
        )
        
    except Exception as e:
        logger.error(f"Gmail test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing test email: {str(e)}"
        )


# ============================================================================
# WHATSAPP WEBHOOKS
# ============================================================================

@router.get("/whatsapp", tags=["WhatsApp"])
async def whatsapp_webhook_verify():
    """
    WhatsApp webhook verification endpoint.
    
    Required by Twilio for webhook configuration.
    Returns 200 OK.
    """
    return Response(status_code=200, content="OK")


@router.post("/whatsapp", tags=["WhatsApp"])
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    To: str = Form(None)
):
    """
    Receive WhatsApp messages from Twilio.
    
    Processes incoming WhatsApp messages and publishes to Kafka.
    
    Args:
        From: Sender phone number.
        Body: Message content.
        MessageSid: Twilio message ID.
        To: Recipient number.
        
    Returns:
        Empty TwiML response.
    """
    try:
        # Create webhook data
        webhook_data = {
            "from": From,
            "body": Body,
            "message_sid": MessageSid,
            "to": To,
            "timestamp": whatsapp_handler._get_timestamp()
        }
        
        # Validate
        if not whatsapp_handler.validate_incoming(webhook_data):
            raise ValueError("Invalid webhook data")
        
        # Normalize
        normalized = whatsapp_handler.normalize_message(webhook_data)
        
        # Publish to Kafka
        producer = FTEKafkaProducer()
        await producer.start()
        
        await producer.publish(TOPICS["tickets_incoming"], normalized)
        
        await producer.stop()
        
        logger.info(f"WhatsApp message processed from {From}")
        
        # Return empty TwiML response
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing WhatsApp webhook: {str(e)}"
        )


@router.post("/whatsapp/test", response_model=WebhookResponse, tags=["WhatsApp"])
async def whatsapp_test(submission: WhatsAppTestSubmission):
    """
    Test endpoint for WhatsApp simulation.
    
    Accepts test message data and publishes to Kafka.
    
    Args:
        submission: Test message data with from_phone and body.
        
    Returns:
        Ticket confirmation.
    """
    try:
        # Create webhook data
        webhook_data = {
            "from": submission.from_phone,
            "body": submission.body,
            "message_sid": whatsapp_handler._generate_message_id("TEST"),
            "timestamp": whatsapp_handler._get_timestamp()
        }
        
        # Normalize
        normalized = whatsapp_handler.normalize_message(webhook_data)
        
        # Publish to Kafka
        producer = FTEKafkaProducer()
        await producer.start()
        
        await producer.publish(TOPICS["tickets_incoming"], normalized)
        
        await producer.stop()
        
        logger.info(f"Test WhatsApp message published from {submission.from_phone}")
        
        return WebhookResponse(
            status="received",
            message="Test WhatsApp message published to Kafka",
            ticket_id=normalized.get("channel_message_id")
        )
        
    except Exception as e:
        logger.error(f"WhatsApp test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing test message: {str(e)}"
        )
