"""
Conversation Memory Module for TechCorp Customer Success AI Agent.

This module provides memory and state management for multi-channel
customer conversations, enabling the agent to remember context across
messages and channels.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class ConversationStatus(Enum):
    """Possible states for a conversation."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    PENDING = "pending"


class SentimentTrend(Enum):
    """Possible sentiment trends for a conversation."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


class ResolutionStatus(Enum):
    """Resolution status for a conversation."""
    SOLVED = "solved"
    PENDING = "pending"
    ESCALATED = "escalated"


@dataclass
class Message:
    """
    Represents a single message in a conversation.
    
    Attributes:
        role: Either "customer" or "agent".
        content: The message text.
        channel: Channel type (email, whatsapp, web_form).
        timestamp: ISO format timestamp when message was sent.
        sentiment_score: Sentiment score (0.0-1.0) at time of message.
    """
    role: str
    content: str
    channel: str
    timestamp: str
    sentiment_score: float
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create Message from dictionary."""
        return cls(**data)


@dataclass
class CustomerState:
    """
    Represents the state of a customer.
    
    Attributes:
        customer_id: Unique customer identifier (email or phone).
        first_contact_channel: Channel used for first contact.
        current_channel: Most recent channel used.
        has_switched_channels: Whether customer has used multiple channels.
        total_messages_sent: Total messages across all conversations.
        is_returning_customer: Whether this is a returning customer.
    """
    customer_id: str
    first_contact_channel: str = ""
    current_channel: str = ""
    has_switched_channels: bool = False
    total_messages_sent: int = 0
    is_returning_customer: bool = False
    
    def to_dict(self) -> Dict:
        """Convert customer state to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomerState':
        """Create CustomerState from dictionary."""
        return cls(**data)


@dataclass
class ConversationState:
    """
    Represents the state of a conversation.
    
    Attributes:
        conversation_id: Unique conversation identifier.
        status: Current conversation status (active, resolved, etc.).
        topics_discussed: List of topics discussed in conversation.
        sentiment_trend: Trend of sentiment over conversation.
        resolution_status: Resolution status (solved, pending, escalated).
        escalation_reason: Reason for escalation if applicable.
        created_at: ISO format timestamp when conversation started.
        updated_at: ISO format timestamp when conversation was last updated.
    """
    conversation_id: str
    status: str = ConversationStatus.ACTIVE.value
    topics_discussed: List[str] = field(default_factory=list)
    sentiment_trend: str = SentimentTrend.STABLE.value
    resolution_status: str = ResolutionStatus.PENDING.value
    escalation_reason: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        """Convert conversation state to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationState':
        """Create ConversationState from dictionary."""
        return cls(**data)


class ConversationMemory:
    """
    Manages conversation history and state for a single customer interaction.
    
    This class tracks:
    - All messages in the current conversation
    - Customer state across channels
    - Conversation state and status
    - Sentiment trends over time
    - Topics discussed
    
    Usage:
        memory = ConversationMemory(customer_id="john@example.com")
        memory.add_message("customer", "I need help", "email", 0.5)
        memory.add_message("agent", "How can I help?", "email", 0.5)
        print(memory.get_summary())
    """
    
    def __init__(self, customer_id: str, storage_dir: str = None):
        """
        Initialize conversation memory for a customer.
        
        Args:
            customer_id: Unique customer identifier (email or phone).
            storage_dir: Directory for storing memory files.
                        Defaults to memory/ relative to project root.
        """
        self.customer_id = customer_id
        self.conversation_id = str(uuid.uuid4())
        
        # Set storage directory
        if storage_dir is None:
            self.storage_dir = Path(__file__).parent.parent.parent / "memory"
        else:
            self.storage_dir = Path(storage_dir)
        
        # Initialize message history
        self._messages: List[Message] = []
        
        # Initialize customer state
        self._customer_state = CustomerState(
            customer_id=customer_id,
            is_returning_customer=False
        )
        
        # Initialize conversation state
        now = datetime.now().isoformat()
        self._conversation_state = ConversationState(
            conversation_id=self.conversation_id,
            created_at=now,
            updated_at=now
        )
        
        # Sentiment history for trend calculation
        self._sentiment_history: List[float] = []
    
    def add_message(self, role: str, content: str, channel: str, 
                    sentiment_score: float) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role ("customer" or "agent").
            content: Message text.
            channel: Channel type (email, whatsapp, web_form).
            sentiment_score: Sentiment score (0.0-1.0).
        """
        message = Message(
            role=role,
            content=content,
            channel=channel,
            timestamp=datetime.now().isoformat(),
            sentiment_score=sentiment_score
        )
        
        self._messages.append(message)
        
        # Update sentiment history
        if role == "customer":
            self._sentiment_history.append(sentiment_score)
            self._calculate_sentiment_trend()

        # Update customer state
        self._update_customer_state(channel)
        
        # Update conversation state
        self._conversation_state.updated_at = datetime.now().isoformat()
    
    def get_history(self) -> List[Dict]:
        """
        Get all messages in the conversation.
        
        Returns:
            List of message dictionaries with role, content, channel,
            timestamp, and sentiment_score.
        """
        return [msg.to_dict() for msg in self._messages]
    
    def get_summary(self) -> str:
        """
        Get a short summary of the conversation so far.
        
        Returns:
            Human-readable summary of conversation.
        """
        if not self._messages:
            return "No messages in conversation yet."
        
        # Count customer vs agent messages
        customer_msgs = sum(1 for m in self._messages if m.role == "customer")
        agent_msgs = sum(1 for m in self._messages if m.role == "agent")
        
        # Get topics
        topics = ", ".join(self._conversation_state.topics_discussed) if self._conversation_state.topics_discussed else "none"
        
        # Get channels used
        channels_used = set(m.channel for m in self._messages)
        
        summary_parts = [
            f"Conversation ID: {self.conversation_id}",
            f"Customer: {self.customer_id}",
            f"Messages: {customer_msgs} from customer, {agent_msgs} from agent",
            f"Channels: {', '.join(channels_used)}",
            f"Topics: {topics}",
            f"Sentiment Trend: {self._conversation_state.sentiment_trend}",
            f"Status: {self._conversation_state.status}"
        ]
        
        return " | ".join(summary_parts)
    
    def update_status(self, new_status: str) -> None:
        """
        Update the conversation status.
        
        Args:
            new_status: New status value (active, resolved, escalated, pending).
        """
        valid_statuses = [s.value for s in ConversationStatus]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
        
        self._conversation_state.status = new_status
        self._conversation_state.updated_at = datetime.now().isoformat()
        
        # Update resolution status based on conversation status
        if new_status == ConversationStatus.RESOLVED.value:
            self._conversation_state.resolution_status = ResolutionStatus.SOLVED.value
        elif new_status == ConversationStatus.ESCALATED.value:
            self._conversation_state.resolution_status = ResolutionStatus.ESCALATED.value
    
    def add_topic(self, topic: str) -> None:
        """
        Add a topic to the list of discussed topics.
        
        Args:
            topic: Topic string to add.
        """
        topic_lower = topic.lower().strip()
        if topic_lower not in [t.lower() for t in self._conversation_state.topics_discussed]:
            self._conversation_state.topics_discussed.append(topic_lower)
        self._conversation_state.updated_at = datetime.now().isoformat()
    
    def update_sentiment_trend(self) -> None:
        """
        Update the sentiment trend based on sentiment history.
        
        Analyzes the last few sentiment scores to determine if
        sentiment is improving, declining, or stable.
        """
        if len(self._sentiment_history) < 2:
            self._conversation_state.sentiment_trend = SentimentTrend.STABLE.value
            return
        
        # Compare recent sentiment to earlier sentiment
        mid_point = len(self._sentiment_history) // 2
        early_avg = sum(self._sentiment_history[:mid_point]) / mid_point if mid_point > 0 else 0
        recent_avg = sum(self._sentiment_history[mid_point:]) / (len(self._sentiment_history) - mid_point)
        
        diff = recent_avg - early_avg
        
        if diff > 0.1:
            self._conversation_state.sentiment_trend = SentimentTrend.IMPROVING.value
        elif diff < -0.1:
            self._conversation_state.sentiment_trend = SentimentTrend.DECLINING.value
        else:
            self._conversation_state.sentiment_trend = SentimentTrend.STABLE.value
        
        self._conversation_state.updated_at = datetime.now().isoformat()
    
    def _calculate_sentiment_trend(self) -> None:
        """
        Internal method to calculate sentiment trend.
        
        Analyzes sentiment history to determine if sentiment
        is improving, declining, or stable.
        """
        if len(self._sentiment_history) < 2:
            self._conversation_state.sentiment_trend = SentimentTrend.STABLE.value
            return
        
        # Compare recent sentiment to earlier sentiment
        mid_point = len(self._sentiment_history) // 2
        early_avg = sum(self._sentiment_history[:mid_point]) / mid_point if mid_point > 0 else 0
        recent_avg = sum(self._sentiment_history[mid_point:]) / (len(self._sentiment_history) - mid_point)
        
        diff = recent_avg - early_avg
        
        if diff > 0.1:
            self._conversation_state.sentiment_trend = SentimentTrend.IMPROVING.value
        elif diff < -0.1:
            self._conversation_state.sentiment_trend = SentimentTrend.DECLINING.value
        else:
            self._conversation_state.sentiment_trend = SentimentTrend.STABLE.value
        
        self._conversation_state.updated_at = datetime.now().isoformat()
    
    def switch_channel(self, new_channel: str) -> None:
        """
        Record a channel switch for the customer.
        
        Args:
            new_channel: New channel type (email, whatsapp, web_form).
        """
        if self._customer_state.current_channel and self._customer_state.current_channel != new_channel:
            self._customer_state.has_switched_channels = True
            self._customer_state.current_channel = new_channel
        elif not self._customer_state.current_channel:
            self._customer_state.current_channel = new_channel
            self._customer_state.first_contact_channel = new_channel
    
    def is_same_customer(self, identifier: str) -> bool:
        """
        Check if an identifier matches the current customer.
        
        Args:
            identifier: Email or phone to check.
            
        Returns:
            True if identifier matches customer_id.
        """
        return identifier.lower().strip() == self.customer_id.lower().strip()
    
    def get_customer_context(self) -> Dict:
        """
        Get full customer context dictionary.
        
        Returns:
            Dictionary with all customer and conversation state.
        """
        return {
            'customer_id': self.customer_id,
            'customer_state': self._customer_state.to_dict(),
            'conversation_state': self._conversation_state.to_dict(),
            'message_count': len(self._messages),
            'sentiment_history': self._sentiment_history.copy(),
            'recent_messages': [m.to_dict() for m in self._messages[-5:]]  # Last 5 messages
        }
    
    def _update_customer_state(self, channel: str) -> None:
        """
        Update customer state based on new message.
        
        Args:
            channel: Channel of the new message.
        """
        # Track channel switching
        if self._customer_state.current_channel and self._customer_state.current_channel != channel:
            self._customer_state.has_switched_channels = True
        
        self._customer_state.current_channel = channel
        
        if not self._customer_state.first_contact_channel:
            self._customer_state.first_contact_channel = channel
        
        self._customer_state.total_messages_sent += 1
        
        # After first message, customer is returning
        if self._customer_state.total_messages_sent > 1:
            self._customer_state.is_returning_customer = True
    
    def set_escalation_reason(self, reason: str) -> None:
        """
        Set the escalation reason for the conversation.
        
        Args:
            reason: Reason for escalation.
        """
        self._conversation_state.escalation_reason = reason
        self._conversation_state.updated_at = datetime.now().isoformat()
    
    def get_topics_discussed(self) -> List[str]:
        """
        Get list of topics discussed in conversation.
        
        Returns:
            List of topic strings.
        """
        return self._conversation_state.topics_discussed.copy()
    
    def get_sentiment_trend(self) -> str:
        """
        Get current sentiment trend.
        
        Returns:
            Sentiment trend string (improving, declining, stable).
        """
        return self._conversation_state.sentiment_trend
    
    def get_status(self) -> str:
        """
        Get current conversation status.
        
        Returns:
            Status string (active, resolved, escalated, pending).
        """
        return self._conversation_state.status
    
    def to_dict(self) -> Dict:
        """
        Convert entire memory state to dictionary.
        
        Returns:
            Complete memory state as dictionary.
        """
        return {
            'customer_id': self.customer_id,
            'conversation_id': self.conversation_id,
            'messages': self.get_history(),
            'customer_state': self._customer_state.to_dict(),
            'conversation_state': self._conversation_state.to_dict(),
            'sentiment_history': self._sentiment_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict, storage_dir: str = None) -> 'ConversationMemory':
        """
        Create ConversationMemory from dictionary.
        
        Args:
            data: Dictionary with memory state.
            storage_dir: Optional storage directory.
            
        Returns:
            ConversationMemory instance with loaded state.
        """
        memory = cls(
            customer_id=data['customer_id'],
            storage_dir=storage_dir
        )
        
        memory.conversation_id = data['conversation_id']
        memory._messages = [Message.from_dict(m) for m in data.get('messages', [])]
        memory._customer_state = CustomerState.from_dict(data.get('customer_state', {}))
        memory._conversation_state = ConversationState.from_dict(data.get('conversation_state', {}))
        memory._sentiment_history = data.get('sentiment_history', [])
        
        return memory
