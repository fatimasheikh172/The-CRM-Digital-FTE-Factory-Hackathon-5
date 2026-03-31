"""Web Form channel handler for website contact form integration."""

from typing import Dict, Optional


class WebFormChannel:
    """
    Handler for Web Form channel integration.
    
    Processes incoming web form submissions and formats outgoing responses
    according to web form-specific guidelines (semi-formal, structured).
    """
    
    def __init__(self):
        """Initialize the Web Form Channel handler."""
        self.channel_type = "web_form"
        self.max_response_length = 500  # words
    
    def parse_incoming(self, raw_submission: Dict) -> Dict:
        """
        Parse an incoming web form submission.
        
        Args:
            raw_submission: Raw form data with 'email', 'subject', 'message' keys.
            
        Returns:
            Parsed message dictionary.
        """
        return {
            'channel': 'web_form',
            'from': raw_submission.get('email', ''),
            'subject': raw_submission.get('subject', ''),
            'message': raw_submission.get('message', raw_submission.get('body', '')),
            'form_type': raw_submission.get('form_type', 'support'),
            'priority': raw_submission.get('priority', 'normal')
        }
    
    def format_outgoing(self, response: str, customer_email: str,
                        ticket_id: str = None) -> Dict:
        """
        Format an outgoing web form response.
        
        Args:
            response: Formatted response text.
            customer_email: Customer's email address.
            ticket_id: Optional ticket reference number.
            
        Returns:
            Dictionary ready for response (email or display).
        """
        return {
            'to': customer_email,
            'message': response,
            'channel': 'web_form',
            'ticket_id': ticket_id
        }
    
    def extract_customer_identifier(self, raw_submission: Dict) -> str:
        """
        Extract customer identifier (email) from form submission.
        
        Args:
            raw_submission: Raw form data.
            
        Returns:
            Customer email address.
        """
        return raw_submission.get('email', '')
