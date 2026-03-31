"""WhatsApp channel handler for WhatsApp Business API integration."""

from typing import Dict


class WhatsAppChannel:
    """
    Handler for WhatsApp channel integration.
    
    Processes incoming WhatsApp messages and formats outgoing responses
    according to WhatsApp-specific guidelines (short, casual).
    """
    
    def __init__(self):
        """Initialize the WhatsApp Channel handler."""
        self.channel_type = "whatsapp"
        self.max_response_length = 3  # sentences
    
    def parse_incoming(self, raw_message: Dict) -> Dict:
        """
        Parse an incoming WhatsApp message.
        
        Args:
            raw_message: Raw WhatsApp message data with 'from', 'body' keys.
            
        Returns:
            Parsed message dictionary.
        """
        return {
            'channel': 'whatsapp',
            'from': raw_message.get('from', ''),
            'message': raw_message.get('body', raw_message.get('message', '')),
            'timestamp': raw_message.get('timestamp', None)
        }
    
    def format_outgoing(self, response: str, customer_phone: str) -> Dict:
        """
        Format an outgoing WhatsApp response.
        
        Args:
            response: Formatted response text (should be short).
            customer_phone: Customer's phone number.
            
        Returns:
            Dictionary ready for WhatsApp sending.
        """
        return {
            'to': customer_phone,
            'message': response,
            'channel': 'whatsapp'
        }
    
    def extract_customer_identifier(self, raw_message: Dict) -> str:
        """
        Extract customer identifier (phone) from incoming message.
        
        Args:
            raw_message: Raw WhatsApp message data.
            
        Returns:
            Customer phone number.
        """
        return raw_message.get('from', '')
