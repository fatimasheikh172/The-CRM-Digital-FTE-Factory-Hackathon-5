"""
Gmail Handler for TechCorp Customer Success AI Agent.

Provides Gmail integration with simulation mode for development.
In simulation mode, emails are saved to JSON files instead of sent via Gmail API.
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

from channels.base_channel import BaseChannel


class GmailHandler(BaseChannel):
    """
    Handler for Gmail (Email) channel integration.
    
    Features:
    - Simulation mode for development (no API credentials needed)
    - Parse incoming emails from Gmail Pub/Sub notifications
    - Format outgoing responses with proper email structure
    - Extract customer information from email headers
    
    Usage:
        handler = GmailHandler(simulation_mode=True)
        normalized = handler.process_incoming_email(raw_email)
        response = handler.format_response("Hello!", {"name": "John"})
        result = handler.send_reply("john@example.com", "Re: Issue", response)
    """
    
    channel_name = "email"
    
    def __init__(self, simulation_mode: bool = True, simulation_dir: str = None):
        """
        Initialize Gmail handler.
        
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
        
        # Email formatting config
        self.max_response_words = 500
        self.signature = "Best regards,\nTechCorp Support Team"
    
    def normalize_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw email to standard format.
        
        Args:
            raw_message: Raw email data with from, subject, body, etc.
            
        Returns:
            Normalized message dictionary.
        """
        # Extract email from "Name <email>" format
        from_header = raw_message.get('from', '')
        customer_email = self.extract_email_from_header(from_header)
        
        # Extract name if present
        customer_name = None
        if ' <' in from_header:
            customer_name = from_header.split(' <')[0].strip().strip('"\'')
        
        return {
            "channel": self.channel_name,
            "customer_email": customer_email,
            "customer_phone": None,
            "customer_name": customer_name,
            "subject": raw_message.get('subject', ''),
            "content": self._clean_text(raw_message.get('body', raw_message.get('message', ''))),
            "channel_message_id": raw_message.get('message_id', self._generate_message_id("EMAIL")),
            "received_at": raw_message.get('received_at', self._get_timestamp()),
            "metadata": {
                "thread_id": raw_message.get('thread_id'),
                "has_attachment": raw_message.get('has_attachment', False),
                "original_from": from_header
            }
        }
    
    def format_response(self, response_text: str, customer_data: Dict[str, Any]) -> str:
        """
        Format response as formal email.
        
        Args:
            response_text: Base response from agent.
            customer_data: Customer info (name, email, etc.)
            
        Returns:
            Formatted email body.
        """
        name = customer_data.get('name') or customer_data.get('customer_name', 'Valued Customer')
        
        # Build email parts
        parts = []
        
        # Formal greeting
        parts.append(f"Dear {name},")
        parts.append("")
        
        # Response body (ensure under word limit)
        words = response_text.split()
        if len(words) > self.max_response_words:
            response_text = ' '.join(words[:self.max_response_words]) + "..."
        
        parts.append(response_text)
        parts.append("")
        
        # Signature
        parts.append(self.signature)
        
        return '\n'.join(parts)
    
    def validate_incoming(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate incoming email data.
        
        Args:
            raw_data: Raw email data.
            
        Returns:
            True if valid.
        """
        # Must have from and body/message
        if not raw_data.get('from'):
            return False
        
        body = raw_data.get('body') or raw_data.get('message')
        if not body or not str(body).strip():
            return False
        
        # Email must be valid format
        from_header = raw_data.get('from', '')
        email = self.extract_email_from_header(from_header)
        if not email or '@' not in email:
            return False
        
        return True
    
    def process_incoming_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming email and return normalized format.
        
        Args:
            email_data: Raw email data from Gmail API or simulation.
            
        Returns:
            Normalized message dictionary.
        """
        if not self.validate_incoming(email_data):
            raise ValueError("Invalid email data")
        
        return self.normalize_message(email_data)
    
    def send_reply(self, to_email: str, subject: str, body: str, 
                   thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email reply.
        
        In simulation mode: saves to simulation/gmail_sent.json
        
        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body: Email body.
            thread_id: Optional Gmail thread ID for threading.
            
        Returns:
            Result dictionary with message_id and status.
        """
        message_id = self._generate_message_id("SENT")
        
        if self.simulation_mode:
            # Save to simulation file
            sent_file = self.simulation_dir / "gmail_sent.json"
            
            # Load existing sent emails
            sent_emails = []
            if sent_file.exists():
                try:
                    with open(sent_file, 'r', encoding='utf-8') as f:
                        sent_emails = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    sent_emails = []
            
            # Add new email
            sent_emails.append({
                "message_id": message_id,
                "to": to_email,
                "subject": subject,
                "body": body,
                "thread_id": thread_id,
                "sent_at": self._get_timestamp(),
                "status": "simulated"
            })
            
            # Save back
            with open(sent_file, 'w', encoding='utf-8') as f:
                json.dump(sent_emails, f, indent=2)
            
            return {
                "channel_message_id": message_id,
                "delivery_status": "simulated",
                "to": to_email,
                "subject": subject
            }
        else:
            # In production, would use Gmail API
            raise NotImplementedError("Production Gmail API not implemented yet")
    
    def parse_pubsub_notification(self, pubsub_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Gmail Pub/Sub push notification.
        
        Args:
            pubsub_data: Pub/Sub notification data.
            
        Returns:
            List of email message dictionaries.
        """
        # In simulation mode, return sample data
        if self.simulation_mode:
            return [self._get_sample_email()]
        
        # In production, would parse actual Pub/Sub message
        # and fetch emails from Gmail API
        return []
    
    def extract_email_from_header(self, from_header: str) -> str:
        """
        Extract clean email from "Name <email>" format.
        
        Args:
            from_header: Email header string.
            
        Returns:
            Clean email address.
        """
        if not from_header:
            return ""
        
        # Handle "Name <email>" format
        match = re.search(r'<([^>]+)>', from_header)
        if match:
            return match.group(1).strip()
        
        # Handle just email
        if '@' in from_header:
            # Extract just the email part
            email = from_header.strip().strip('"\'')
            return email.split(' ')[0] if ' ' in email else email
        
        return ""
    
    def _get_sample_email(self) -> Dict[str, Any]:
        """Get a sample email for simulation."""
        return {
            "from": "John Doe <john.doe@example.com>",
            "subject": "Cannot login to my account",
            "body": "Hi, I've been trying to login but keep getting an error. Can you help?",
            "message_id": self._generate_message_id("SAMPLE"),
            "thread_id": "thread_123",
            "received_at": self._get_timestamp(),
            "has_attachment": False
        }


# Convenience function for quick access
def create_gmail_handler(simulation_mode: bool = True) -> GmailHandler:
    """
    Create a Gmail handler instance.
    
    Args:
        simulation_mode: Use simulation mode.
        
    Returns:
        GmailHandler instance.
    """
    return GmailHandler(simulation_mode=simulation_mode)
