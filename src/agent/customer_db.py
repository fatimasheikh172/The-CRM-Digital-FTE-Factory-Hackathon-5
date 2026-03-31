"""
Customer Database Module for TechCorp Customer Success AI Agent.

This module provides persistent storage for customer data and conversation
history using JSON files. It simulates a database for the prototype.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class CustomerDatabase:
    """
    Manages customer data and conversation history using JSON files.
    
    This class provides:
    - Customer record storage and retrieval
    - Conversation history persistence
    - Cross-channel customer recognition
    - Customer lookup by email or phone
    
    Data is stored in:
    - memory/customers.json: Customer records
    - memory/conversations.json: Conversation history
    
    Usage:
        db = CustomerDatabase()
        customer = db.get_or_create_customer("john@example.com", "email")
        db.save_conversation(customer['customer_id'], conversation_data)
        history = db.get_customer_history(customer['customer_id'])
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize the customer database.
        
        Args:
            storage_dir: Directory for storing JSON files.
                        Defaults to memory/ relative to project root.
        """
        if storage_dir is None:
            self.storage_dir = Path(__file__).parent.parent.parent / "memory"
        else:
            self.storage_dir = Path(storage_dir)
        
        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.customers_file = self.storage_dir / "customers.json"
        self.conversations_file = self.storage_dir / "conversations.json"
        
        # Initialize files if they don't exist
        self._init_files()
        
        # In-memory cache
        self._customers_cache: Dict[str, Dict] = {}
        self._conversations_cache: Dict[str, Dict] = {}
        
        # Load data from files
        self._load_data()
    
    def _init_files(self) -> None:
        """
        Initialize JSON files if they don't exist.
        
        Creates empty JSON arrays in customers.json and conversations.json
        if they don't already exist.
        """
        try:
            if not self.customers_file.exists():
                with open(self.customers_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2)
            
            if not self.conversations_file.exists():
                with open(self.conversations_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database files: {e}")
    
    def _load_data(self) -> None:
        """
        Load customer and conversation data from JSON files.
        
        Populates the in-memory caches with data from disk.
        """
        try:
            # Load customers
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                customers = json.load(f)
                self._customers_cache = {c['customer_id']: c for c in customers}
            
            # Load conversations
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
                self._conversations_cache = {c['conversation_id']: c for c in conversations}
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse database files: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load database files: {e}")
    
    def _save_data(self) -> None:
        """
        Save customer and conversation data to JSON files.
        
        Writes the in-memory caches to disk.
        """
        try:
            # Save customers
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(list(self._customers_cache.values()), f, indent=2, default=str)
            
            # Save conversations
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(list(self._conversations_cache.values()), f, indent=2, default=str)
        except Exception as e:
            raise RuntimeError(f"Failed to save database files: {e}")
    
    def _normalize_identifier(self, identifier: str) -> str:
        """
        Normalize an email or phone identifier.
        
        Args:
            identifier: Email or phone string.
            
        Returns:
            Normalized identifier (lowercase for email, cleaned for phone).
        """
        identifier = identifier.strip()
        
        # Check if email
        if '@' in identifier:
            return identifier.lower()
        
        # Phone number - clean and normalize
        cleaned = ''.join(c for c in identifier if c.isdigit() or c == '+')
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        return cleaned
    
    def find_customer(self, email: str = None, phone: str = None) -> Optional[Dict]:
        """
        Find a customer by email or phone number.
        
        Args:
            email: Customer email address.
            phone: Customer phone number.
            
        Returns:
            Customer dictionary if found, None otherwise.
        """
        identifier = email or phone
        
        if not identifier:
            return None
        
        identifier = self._normalize_identifier(identifier)
        
        # Search by identifier (email or phone stored as primary key)
        for customer in self._customers_cache.values():
            if customer.get('email') and self._normalize_identifier(customer['email']) == identifier:
                return customer
            if customer.get('phone') and self._normalize_identifier(customer['phone']) == identifier:
                return customer
            # Also check customer_id which might be the email/phone
            if self._normalize_identifier(customer.get('customer_id', '')) == identifier:
                return customer
        
        return None
    
    def create_customer(self, identifier: str, channel: str) -> Dict:
        """
        Create a new customer record.
        
        Args:
            identifier: Customer email or phone number.
            channel: Channel of first contact (email, whatsapp, web_form).
            
        Returns:
            New customer dictionary.
        """
        identifier = self._normalize_identifier(identifier)
        customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        
        # Determine if email or phone
        is_email = '@' in identifier
        
        customer = {
            'customer_id': customer_id,
            'email': identifier if is_email else None,
            'phone': identifier if not is_email else None,
            'primary_identifier': identifier,
            'first_channel': channel,
            'first_contact': datetime.now().isoformat(),
            'total_conversations': 0,
            'total_messages': 0,
            'conversations': [],
            'last_contact': datetime.now().isoformat(),
            'channels_used': [channel]
        }
        
        self._customers_cache[customer_id] = customer
        self._save_data()
        
        return customer
    
    def get_or_create_customer(self, identifier: str, channel: str) -> Dict:
        """
        Get existing customer or create new one.
        
        Args:
            identifier: Customer email or phone number.
            channel: Channel of contact.
            
        Returns:
            Customer dictionary (existing or newly created).
        """
        customer = self.find_customer(email=identifier if '@' in identifier else None,
                                       phone=identifier if '@' not in identifier else None)
        
        if customer:
            # Update last contact and channels
            customer['last_contact'] = datetime.now().isoformat()
            if channel not in customer.get('channels_used', []):
                customer['channels_used'].append(channel)
            self._save_data()
            return customer
        
        # Create new customer
        return self.create_customer(identifier, channel)
    
    def save_conversation(self, customer_id: str, conversation: Dict) -> str:
        """
        Save a conversation to the database.
        
        Args:
            customer_id: Customer ID to associate conversation with.
            conversation: Conversation data dictionary.
            
        Returns:
            Conversation ID.
        """
        conversation_id = conversation.get('conversation_id', f"CONV-{uuid.uuid4().hex[:8].upper()}")
        
        conversation_record = {
            'conversation_id': conversation_id,
            'customer_id': customer_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'data': conversation
        }
        
        # Save conversation
        self._conversations_cache[conversation_id] = conversation_record
        
        # Update customer record
        if customer_id in self._customers_cache:
            customer = self._customers_cache[customer_id]
            if conversation_id not in customer.get('conversations', []):
                customer['conversations'].append(conversation_id)
            customer['total_conversations'] = len(customer['conversations'])
            
            # Update total messages
            message_count = len(conversation.get('messages', []))
            customer['total_messages'] = customer.get('total_messages', 0) + message_count
        
        self._save_data()
        
        return conversation_id
    
    def get_customer_history(self, customer_id: str) -> List[Dict]:
        """
        Get all past conversations for a customer.
        
        Args:
            customer_id: Customer ID to get history for.
            
        Returns:
            List of conversation dictionaries.
        """
        if customer_id not in self._customers_cache:
            return []
        
        customer = self._customers_cache[customer_id]
        conversations = []
        
        for conv_id in customer.get('conversations', []):
            if conv_id in self._conversations_cache:
                conversations.append(self._conversations_cache[conv_id])
        
        # Sort by updated_at descending (most recent first)
        conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return conversations
    
    def update_conversation(self, conversation_id: str, updates: Dict) -> None:
        """
        Update an existing conversation.
        
        Args:
            conversation_id: ID of conversation to update.
            updates: Dictionary of fields to update.
        """
        if conversation_id not in self._conversations_cache:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        conversation = self._conversations_cache[conversation_id]
        
        # Update data
        if 'data' in updates:
            conversation['data'].update(updates['data'])
        
        # Update timestamp
        conversation['updated_at'] = datetime.now().isoformat()
        
        self._conversations_cache[conversation_id] = conversation
        self._save_data()
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a specific conversation by ID.
        
        Args:
            conversation_id: ID of conversation to retrieve.
            
        Returns:
            Conversation dictionary if found, None otherwise.
        """
        return self._conversations_cache.get(conversation_id)
    
    def get_active_conversation(self, customer_id: str) -> Optional[Dict]:
        """
        Get the most recent active conversation for a customer.
        
        Args:
            customer_id: Customer ID to search for.
            
        Returns:
            Active conversation dictionary if found, None otherwise.
        """
        if customer_id not in self._customers_cache:
            return None
        
        customer = self._customers_cache[customer_id]
        
        # Check conversations in reverse order (most recent first)
        for conv_id in reversed(customer.get('conversations', [])):
            if conv_id in self._conversations_cache:
                conv = self._conversations_cache[conv_id]
                status = conv.get('data', {}).get('conversation_state', {}).get('status', '')
                if status == 'active':
                    return conv
        
        return None
    
    def list_customers(self) -> List[Dict]:
        """
        List all customers in the database.
        
        Returns:
            List of all customer dictionaries.
        """
        return list(self._customers_cache.values())
    
    def delete_customer(self, customer_id: str) -> bool:
        """
        Delete a customer and their conversations.
        
        Args:
            customer_id: ID of customer to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if customer_id not in self._customers_cache:
            return False
        
        customer = self._customers_cache[customer_id]
        
        # Delete associated conversations
        for conv_id in customer.get('conversations', []):
            if conv_id in self._conversations_cache:
                del self._conversations_cache[conv_id]
        
        # Delete customer
        del self._customers_cache[customer_id]
        
        self._save_data()
        
        return True
    
    def get_customer_by_identifier(self, identifier: str) -> Optional[Dict]:
        """
        Get customer by normalized identifier.
        
        Args:
            identifier: Email or phone number.
            
        Returns:
            Customer dictionary if found, None otherwise.
        """
        identifier = self._normalize_identifier(identifier)
        
        for customer in self._customers_cache.values():
            primary = customer.get('primary_identifier', '')
            if self._normalize_identifier(primary) == identifier:
                return customer
        
        return None
    
    def clear_all_data(self) -> None:
        """
        Clear all data from the database.
        
        WARNING: This deletes all customers and conversations.
        """
        self._customers_cache = {}
        self._conversations_cache = {}
        self._save_data()
    
    def get_stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database stats.
        """
        return {
            'total_customers': len(self._customers_cache),
            'total_conversations': len(self._conversations_cache),
            'storage_dir': str(self.storage_dir),
            'customers_file': str(self.customers_file),
            'conversations_file': str(self.conversations_file)
        }
