"""
Channels Module for TechCorp Customer Success AI Agent.

Provides channel handlers for:
- Gmail (Email)
- WhatsApp (Twilio)
- Web Form (FastAPI)
"""

from channels.base_channel import BaseChannel
from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from channels.web_form_handler import WebFormHandler

__all__ = [
    'BaseChannel',
    'GmailHandler',
    'WhatsAppHandler',
    'WebFormHandler'
]
