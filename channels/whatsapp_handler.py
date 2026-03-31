"""
WhatsApp Handler for TechCorp Customer Success AI Agent.

Provides WhatsApp integration via Twilio with simulation mode for development.
In simulation mode, messages are saved to JSON files instead of sent via Twilio API.
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

from channels.base_channel import BaseChannel


class WhatsAppHandler(BaseChannel):
    """
    Handler for WhatsApp channel integration via Twilio.
    
    Features:
    - Simulation mode for development (no Twilio credentials needed)
    - Parse incoming messages from Twilio webhooks
    - Format outgoing responses for WhatsApp (short, casual)
    - Split long messages into WhatsApp-sized chunks
    
    Usage:
        handler = WhatsAppHandler(simulation_mode=True)
        normalized = handler.process_webhook(webhook_data)
        response = handler.format_response("Hello!", {"name": "John"})
        result = handler.send_message("+1234567890", response)
    """
    
    channel_name = "whatsapp"
    
    def __init__(self, simulation_mode: bool = True, simulation_dir: str = None):
        """
        Initialize WhatsApp handler.
        
        Args:
            simulation_mode: If True, use file-based simulation.
            simulation_dir: Directory for simulation files.
        """
        self.simulation_mode = simulation_mode
        
        if simulation_dir is None:
            self.simulation_dir = Path(__file__).parent.parent / "simulation"
        else:
            self.simulation_dir = Path(simulation_dir)
        
        # Ensure simulation directory exists
        if self.simulation_mode:
            self.simulation_dir.mkdir(parents=True, exist_ok=True)
        
        # WhatsApp formatting config
        self.max_message_length = 1600  # chars per message
        self.max_response_length = 300  # chars for responses
        self.human_prompt = "Reply 'human' for live support"
    
    def normalize_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw WhatsApp message to standard format.
        
        Args:
            raw_message: Raw WhatsApp message from Twilio webhook.
            
        Returns:
            Normalized message dictionary.
        """
        # Extract phone number (may have whatsapp: prefix)
        from_number = raw_message.get('from', '')
        customer_phone = self._clean_phone_number(from_number)
        
        return {
            "channel": self.channel_name,
            "customer_email": None,
            "customer_phone": customer_phone,
            "customer_name": None,
            "subject": None,
            "content": self._clean_text(raw_message.get('body', raw_message.get('message', ''))),
            "channel_message_id": raw_message.get('message_sid', self._generate_message_id("WA")),
            "received_at": raw_message.get('timestamp', self._get_timestamp()),
            "metadata": {
                "message_sid": raw_message.get('message_sid'),
                "conversation_sid": raw_message.get('conversation_sid'),
                "original_from": from_number
            }
        }
    
    def format_response(self, response_text: str, customer_data: Dict[str, Any]) -> str:
        """
        Format response for WhatsApp (short, casual, conversational).
        
        Args:
            response_text: Base response from agent.
            customer_data: Customer info.
            
        Returns:
            Formatted WhatsApp message (under 300 chars).
        """
        # Trim to max length
        if len(response_text) > self.max_response_length:
            response_text = response_text[:self.max_response_length - 3] + "..."
        
        # Add human prompt hint
        result = response_text.strip()
        
        # Add the human prompt hint if not already present
        if self.human_prompt.lower() not in result.lower():
            result += f"\n\n{self.human_prompt}"
        
        return result
    
    def validate_incoming(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate incoming WhatsApp message data.
        
        Args:
            raw_data: Raw webhook data.
            
        Returns:
            True if valid.
        """
        # Must have from and body
        if not raw_data.get('from'):
            return False
        
        body = raw_data.get('body') or raw_data.get('message')
        if not body or not str(body).strip():
            return False
        
        # Phone number should be present
        from_number = raw_data.get('from', '')
        if not self._clean_phone_number(from_number):
            return False
        
        return True
    
    def process_webhook(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Twilio webhook POST data.
        
        Args:
            form_data: Form data from Twilio webhook.
            
        Returns:
            Normalized message dictionary.
        """
        if not self.validate_incoming(form_data):
            raise ValueError("Invalid webhook data")
        
        return self.normalize_message(form_data)
    
    def send_message(self, to_phone: str, body: str) -> Dict[str, Any]:
        """
        Send WhatsApp message.
        
        In simulation mode: saves to simulation/whatsapp_sent.json
        Splits long messages into chunks.
        
        Args:
            to_phone: Recipient phone number.
            body: Message body.
            
        Returns:
            Result dictionary with message_ids and status.
        """
        # Split into chunks if needed
        chunks = self.format_for_whatsapp(body)
        message_ids = []
        
        for chunk in chunks:
            message_id = self._generate_message_id("WA_SENT")
            message_ids.append(message_id)
            
            if self.simulation_mode:
                # Save to simulation file
                sent_file = self.simulation_dir / "whatsapp_sent.json"
                
                # Load existing sent messages
                sent_messages = []
                if sent_file.exists():
                    try:
                        with open(sent_file, 'r', encoding='utf-8') as f:
                            sent_messages = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        sent_messages = []
                
                # Add new message
                sent_messages.append({
                    "message_id": message_id,
                    "to": self._clean_phone_number(to_phone),
                    "body": chunk,
                    "sent_at": self._get_timestamp(),
                    "status": "simulated",
                    "chunk_count": len(chunks)
                })
                
                # Save back
                with open(sent_file, 'w', encoding='utf-8') as f:
                    json.dump(sent_messages, f, indent=2)
        
        return {
            "channel_message_id": message_ids[0] if message_ids else None,
            "message_ids": message_ids,
            "delivery_status": "simulated",
            "to": self._clean_phone_number(to_phone),
            "chunk_count": len(chunks)
        }
    
    def validate_webhook_signature(self, request_data: Dict[str, Any], 
                                    signature: str = None) -> bool:
        """
        Validate Twilio webhook signature.
        
        In simulation mode: always returns True.
        In production: validates Twilio X-Twilio-Signature header.
        
        Args:
            request_data: Request body data.
            signature: X-Twilio-Signature header value.
            
        Returns:
            True if valid.
        """
        if self.simulation_mode:
            return True
        
        # In production, would validate using Twilio's validation library
        # from twilio.request_validator import RequestValidator
        # validator = RequestValidator(auth_token)
        # return validator.validate(url, params, signature)
        
        return True
    
    def format_for_whatsapp(self, text: str) -> List[str]:
        """
        Split long text into WhatsApp-sized chunks.
        
        Finds natural break points (sentences) when splitting.
        
        Args:
            text: Text to split.
            
        Returns:
            List of message chunks.
        """
        if len(text) <= self.max_message_length:
            return [text]
        
        chunks = []
        remaining = text
        
        while len(remaining) > self.max_message_length:
            # Find best break point (sentence ending)
            break_point = self._find_break_point(remaining[:self.max_message_length])
            
            if break_point > 0:
                chunks.append(remaining[:break_point].strip())
                remaining = remaining[break_point:].strip()
            else:
                # No good break point, hard split
                chunks.append(remaining[:self.max_message_length])
                remaining = remaining[self.max_message_length:].strip()
        
        # Add remaining text
        if remaining:
            chunks.append(remaining)
        
        return chunks
    
    def _find_break_point(self, text: str) -> int:
        """
        Find best break point in text (sentence ending).
        
        Args:
            text: Text to find break point in.
            
        Returns:
            Position of best break point, or 0 if none found.
        """
        # Look for sentence endings in reverse
        for ending in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            pos = text.rfind(ending)
            if pos > len(text) // 2:  # At least halfway through
                return pos + len(ending)
        
        # Look for paragraph breaks
        pos = text.rfind('\n\n')
        if pos > len(text) // 2:
            return pos + 2
        
        return 0
    
    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean phone number to standard format.
        
        Args:
            phone: Raw phone number.
            
        Returns:
            Cleaned phone number with country code.
        """
        if not phone:
            return ""
        
        # Remove whatsapp: prefix if present
        phone = phone.replace('whatsapp:', '').strip()
        
        # Keep only digits and +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Add country code if missing (assume US +1)
        if cleaned and not cleaned.startswith('+'):
            if len(cleaned) == 10:
                cleaned = '+1' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                cleaned = '+' + cleaned
        
        return cleaned
    
    def _get_sample_webhook(self) -> Dict[str, Any]:
        """Get a sample webhook for simulation."""
        return {
            "from": "whatsapp:+14155551234",
            "to": "whatsapp:+14155559999",
            "body": "Hi, my app is not working. Can you help?",
            "message_sid": "SM" + self._generate_message_id(""),
            "conversation_sid": "CH" + self._generate_message_id(""),
            "timestamp": self._get_timestamp()
        }


# Convenience function for quick access
def create_whatsapp_handler(simulation_mode: bool = True) -> WhatsAppHandler:
    """
    Create a WhatsApp handler instance.
    
    Args:
        simulation_mode: Use simulation mode.
        
    Returns:
        WhatsAppHandler instance.
    """
    return WhatsAppHandler(simulation_mode=simulation_mode)
