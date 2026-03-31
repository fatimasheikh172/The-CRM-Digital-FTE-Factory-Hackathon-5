"""Email channel handler for Gmail integration."""

from typing import Dict, Optional


class EmailChannel:
    """
    Handler for email channel (Gmail) integration.
    
    Processes incoming emails and formats outgoing responses
    according to email-specific guidelines.
    """
    
    def __init__(self):
        """Initialize the Email Channel handler."""
        self.channel_type = "email"
        self.max_response_length = 300  # words
    
    def parse_incoming(self, raw_email: Dict) -> Dict:
        """
        Parse an incoming email message.
        
        Args:
            raw_email: Raw email data with 'from', 'subject', 'body' keys.
            
        Returns:
            Parsed message dictionary.
        """
        return {
            'channel': 'email',
            'from': raw_email.get('from', ''),
            'subject': raw_email.get('subject', ''),
            'message': raw_email.get('body', raw_email.get('message', '')),
            'has_attachment': raw_email.get('has_attachment', False)
        }
    
    def format_outgoing(self, response: str, customer_email: str, 
                        subject: str = None) -> Dict:
        """
        Format an outgoing email response.
        
        Args:
            response: Formatted response text.
            customer_email: Customer's email address.
            subject: Email subject (Re: original subject).
            
        Returns:
            Dictionary ready for email sending.
        """
        return {
            'to': customer_email,
            'subject': subject or 'Re: Your Support Request',
            'body': response,
            'channel': 'email'
        }
    
    def extract_customer_identifier(self, raw_email: Dict) -> str:
        """
        Extract customer identifier (email) from incoming email.
        
        Args:
            raw_email: Raw email data.
            
        Returns:
            Customer email address.
        """
        return raw_email.get('from', '')
