"""Customer Identification Skill for identifying and retrieving customer info."""

import hashlib
from typing import Dict, Optional


class CustomerIdentificationSkill:
    """
    Skill for identifying customers based on email or phone number.
    
    In a production system, this would query a customer database.
    For this prototype, it uses an in-memory simulation.
    """
    
    # Simulated customer database
    # In production, this would be a real database query
    _simulated_customers = {
        'john@example.com': {
            'customer_id': 'CUST-001',
            'name': 'John Doe',
            'plan': 'Pro',
            'signup_date': '2024-01-15',
            'ticket_count': 3,
            'last_contact': '2024-02-20'
        },
        'sara@business.com': {
            'customer_id': 'CUST-002',
            'name': 'Sara Smith',
            'plan': 'Enterprise',
            'signup_date': '2023-06-10',
            'ticket_count': 8,
            'last_contact': '2024-03-01'
        },
        'angry@customer.com': {
            'customer_id': 'CUST-003',
            'name': 'Angry Customer',
            'plan': 'Starter',
            'signup_date': '2024-02-01',
            'ticket_count': 5,
            'last_contact': '2024-03-05'
        },
        'dev@startup.com': {
            'customer_id': 'CUST-004',
            'name': 'Dev User',
            'plan': 'Pro',
            'signup_date': '2023-11-20',
            'ticket_count': 12,
            'last_contact': '2024-02-28'
        },
        'newuser@gmail.com': {
            'customer_id': 'CUST-005',
            'name': 'New User',
            'plan': 'Starter',
            'signup_date': '2024-03-08',
            'ticket_count': 0,
            'last_contact': None
        }
    }
    
    # Simulated phone to customer mapping
    _simulated_phones = {
        '+1234567890': 'CUST-006',
        '+9876543210': 'CUST-007',
        '+1122334455': 'CUST-008'
    }
    
    def __init__(self):
        """Initialize the Customer Identification Skill."""
        pass
    
    def identify(self, email: str = None, phone: str = None) -> Dict:
        """
        Identify a customer based on email or phone number.
        
        Args:
            email: Customer email address.
            phone: Customer phone number.
            
        Returns:
            Dictionary with 'customer_id', 'is_new_customer', 'history_summary',
            and 'customer_info' (if found).
        """
        customer_info = None
        customer_id = None
        
        # Try to identify by email first
        if email:
            email_lower = email.lower().strip()
            customer_info = self._simulated_customers.get(email_lower)
            
            if customer_info:
                customer_id = customer_info['customer_id']
        
        # If not found by email, try phone
        if not customer_info and phone:
            phone_clean = self._clean_phone_number(phone)
            customer_id = self._simulated_phones.get(phone_clean)
            
            if customer_id:
                # Get customer info from ID
                for info in self._simulated_customers.values():
                    if info['customer_id'] == customer_id:
                        customer_info = info
                        break
        
        # Determine if new customer
        is_new_customer = customer_info is None
        
        # Generate customer ID for new customers
        if is_new_customer:
            # Generate a pseudo-ID based on email/phone
            identifier = email or phone or 'unknown'
            customer_id = f"NEW-{hashlib.md5(identifier.encode()).hexdigest()[:8].upper()}"
        
        # Build history summary
        history_summary = self._build_history_summary(customer_info, is_new_customer)
        
        return {
            'customer_id': customer_id,
            'is_new_customer': is_new_customer,
            'history_summary': history_summary,
            'customer_info': customer_info
        }
    
    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean and normalize a phone number.
        
        Args:
            phone: Raw phone number string.
            
        Returns:
            Normalized phone number.
        """
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Ensure starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return cleaned
    
    def _build_history_summary(self, customer_info: Optional[Dict], is_new: bool) -> str:
        """
        Build a summary of customer history.
        
        Args:
            customer_info: Customer information dictionary.
            is_new: Whether this is a new customer.
            
        Returns:
            History summary string.
        """
        if is_new:
            return "New customer - no previous history"
        
        if not customer_info:
            return "No history available"
        
        plan = customer_info.get('plan', 'Unknown')
        ticket_count = customer_info.get('ticket_count', 0)
        last_contact = customer_info.get('last_contact', 'Never')
        
        if last_contact is None:
            last_contact = 'First contact'
        
        return f"{plan} plan customer. {ticket_count} previous tickets. Last contact: {last_contact}."
