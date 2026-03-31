"""
Base Channel Class for TechCorp Customer Success AI Agent.

Provides a common interface for all channel handlers:
- Gmail (Email)
- WhatsApp (Twilio)
- Web Form (FastAPI)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime


class BaseChannel(ABC):
    """
    Abstract base class for all channel handlers.
    
    All channel handlers must implement:
    - normalize_message(): Convert raw message to standard format
    - format_response(): Format response for this channel
    - validate_incoming(): Validate incoming message data
    """
    
    channel_name: str = "base"
    
    @abstractmethod
    def normalize_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw message from this channel to standard format.
        
        Standard format:
        {
            "channel": "email/whatsapp/web_form",
            "customer_email": str or None,
            "customer_phone": str or None,
            "customer_name": str or None,
            "subject": str or None,
            "content": str,
            "channel_message_id": str,
            "received_at": str (ISO timestamp),
            "metadata": dict
        }
        
        Args:
            raw_message: Raw message data from channel.
            
        Returns:
            Normalized message dictionary.
        """
        pass
    
    @abstractmethod
    def format_response(self, response_text: str, customer_data: Dict[str, Any]) -> str:
        """
        Format a response for this specific channel.
        
        Args:
            response_text: Base response text from agent.
            customer_data: Customer information for personalization.
            
        Returns:
            Formatted response string for this channel.
        """
        pass
    
    @abstractmethod
    def validate_incoming(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that incoming message data is valid.
        
        Args:
            raw_data: Raw incoming message data.
            
        Returns:
            True if valid, False otherwise.
        """
        pass
    
    def extract_customer_identifier(self, raw_message: Dict[str, Any]) -> Optional[str]:
        """
        Extract customer identifier (email or phone) from message.
        
        Args:
            raw_message: Raw message data.
            
        Returns:
            Customer email or phone, or None if not found.
        """
        normalized = self.normalize_message(raw_message)
        return normalized.get('customer_email') or normalized.get('customer_phone')
    
    def get_channel_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this channel.
        
        Returns:
            Dictionary with channel info.
        """
        return {
            'channel_name': self.channel_name,
            'class_name': self.__class__.__name__
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean.
            
        Returns:
            Cleaned text.
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = ' '.join(text.split())
        
        # Remove control characters
        cleaned = ''.join(c for c in cleaned if ord(c) >= 32 or c in '\n\t')
        
        return cleaned.strip()
    
    def _generate_message_id(self, prefix: str = "MSG") -> str:
        """
        Generate a unique message ID.
        
        Args:
            prefix: ID prefix.
            
        Returns:
            Unique message ID.
        """
        import uuid
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            ISO format timestamp.
        """
        return datetime.now().isoformat()
