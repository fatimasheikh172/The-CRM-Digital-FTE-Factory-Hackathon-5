"""
TechCorp Customer Success AI Agent Prototype

A production-grade multi-channel support agent that handles customer queries
across Email, WhatsApp, and Web Form channels.

This version includes memory and state management for:
- Conversation history tracking
- Cross-channel customer recognition
- Sentiment trend analysis
- Topic tracking across messages
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict

# Import skills
from skills.knowledge_retrieval import KnowledgeRetrievalSkill
from skills.sentiment_analysis import SentimentAnalysisSkill
from skills.escalation_decision import EscalationDecisionSkill
from skills.channel_adaptation import ChannelAdaptationSkill
from skills.customer_identification import CustomerIdentificationSkill

# Import channel handlers
from src.channels.email_channel import EmailChannel
from src.channels.whatsapp_channel import WhatsAppChannel
from src.channels.web_form_channel import WebFormChannel

# Import memory system
from src.agent.memory import ConversationMemory
from src.agent.customer_db import CustomerDatabase


@dataclass
class AgentResponse:
    """Structured response from the AI agent."""
    response_text: str
    should_escalate: bool
    escalation_reason: Optional[str]
    sentiment_score: float
    channel_used: str
    customer_id: Optional[str] = None
    is_new_customer: bool = False
    processing_time_ms: int = 0
    # Memory-related fields
    is_returning_customer: bool = False
    conversation_id: Optional[str] = None
    sentiment_trend: str = "stable"
    topics_discussed: List[str] = None
    previous_topics: List[str] = None
    has_switched_channels: bool = False


class CustomerSuccessAgent:
    """
    Main Customer Success AI Agent for TechCorp.
    
    Handles multi-channel customer support with:
    - Message normalization
    - Intent extraction
    - Knowledge base search
    - Channel-specific response formatting
    - Escalation decision making
    - Memory and state management
    """
    
    def __init__(self, context_dir: str = None, memory_dir: str = None):
        """
        Initialize the Customer Success Agent.
        
        Args:
            context_dir: Path to context directory with docs and rules.
                        Defaults to ../context relative to this file.
            memory_dir: Path to memory directory for storing conversation data.
                       Defaults to ../memory relative to this file.
        """
        if context_dir is None:
            self.context_dir = Path(__file__).parent.parent.parent / "context"
        else:
            self.context_dir = Path(context_dir)
        
        if memory_dir is None:
            self.memory_dir = Path(__file__).parent.parent.parent / "memory"
        else:
            self.memory_dir = Path(memory_dir)
        
        # Initialize all skills
        self.knowledge_skill = KnowledgeRetrievalSkill(
            self.context_dir / "product-docs.md"
        )
        self.sentiment_skill = SentimentAnalysisSkill()
        self.escalation_skill = EscalationDecisionSkill(
            self.context_dir / "escalation-rules.md"
        )
        self.channel_skill = ChannelAdaptationSkill(
            self.context_dir / "brand-voice.md"
        )
        self.customer_skill = CustomerIdentificationSkill()
        
        # Initialize channel handlers
        self.channels = {
            'email': EmailChannel(),
            'whatsapp': WhatsAppChannel(),
            'web_form': WebFormChannel()
        }
        
        # Initialize memory system
        self.customer_db = CustomerDatabase(str(self.memory_dir))
        self._active_memories: Dict[str, ConversationMemory] = {}
    
    def _get_or_create_memory(self, customer_id: str, channel: str) -> ConversationMemory:
        """
        Get existing conversation memory or create new one.
        
        Args:
            customer_id: Customer identifier.
            channel: Current channel.
            
        Returns:
            ConversationMemory instance.
        """
        # Check if we have an active memory for this customer
        if customer_id in self._active_memories:
            memory = self._active_memories[customer_id]
            memory.switch_channel(channel)
            return memory
        
        # Check database for existing customer
        customer = self.customer_db.get_customer_by_identifier(customer_id)
        
        if customer:
            # Check for active conversation
            active_conv = self.customer_db.get_active_conversation(customer['customer_id'])
            
            if active_conv:
                # Load existing memory
                memory = ConversationMemory.from_dict(
                    active_conv['data'],
                    str(self.memory_dir)
                )
                memory.switch_channel(channel)
                self._active_memories[customer_id] = memory
                return memory
        
        # Create new memory
        memory = ConversationMemory(customer_id, str(self.memory_dir))
        memory.switch_channel(channel)
        self._active_memories[customer_id] = memory
        return memory
    
    def _save_memory(self, memory: ConversationMemory) -> None:
        """
        Save conversation memory to database.
        
        Args:
            memory: ConversationMemory to save.
        """
        customer = self.customer_db.get_or_create_customer(
            memory.customer_id,
            memory._customer_state.current_channel
        )
        
        self.customer_db.save_conversation(
            customer['customer_id'],
            memory.to_dict()
        )
    
    def _extract_topics(self, message: str) -> List[str]:
        """
        Extract topics from a message.
        
        Args:
            message: Message text.
            
        Returns:
            List of topic strings.
        """
        topics = []
        message_lower = message.lower()
        
        # Topic keywords mapping
        topic_keywords = {
            'login': ['login', 'log in', 'sign in', 'password', 'credentials'],
            'billing': ['billing', 'payment', 'invoice', 'charge', 'refund', 'money'],
            'api': ['api', 'integration', 'endpoint', 'rate limit', 'developer'],
            'technical': ['not working', 'broken', 'error', 'bug', 'issue', 'problem'],
            'onboarding': ['getting started', 'invite', 'team', 'setup', 'create'],
            'pricing': ['price', 'plan', 'cost', 'subscription', 'upgrade'],
            'account': ['account', 'profile', 'settings', 'workspace']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _generate_memory_aware_response(self, message: str, channel: str,
                                        memory: ConversationMemory) -> str:
        """
        Generate response that considers conversation history.
        
        Args:
            message: Customer message.
            channel: Channel type.
            memory: Conversation memory.
            
        Returns:
            Context-aware response text.
        """
        context = memory.get_customer_context()
        customer_state = context['customer_state']
        conversation_state = context['conversation_state']
        
        response_parts = []
        
        # Check if returning customer with channel switch
        if customer_state['is_returning_customer'] and customer_state['has_switched_channels']:
            previous_channel = customer_state['first_contact_channel']
            topics = conversation_state.get('topics_discussed', [])
            
            if topics:
                # Reference previous conversation
                response_parts.append(
                    f"I see you contacted us earlier via {previous_channel} about {', '.join(topics)}. "
                    f"How can I help you today?"
                )
        
        # Check sentiment trend
        sentiment_trend = conversation_state.get('sentiment_trend', 'stable')
        
        if sentiment_trend == 'declining':
            # Add empathy for declining sentiment
            response_parts.append(
                "I understand this has been frustrating. Let me help you resolve this."
            )
        
        # Generate base response
        normalized_message = self._normalize_message(message)
        relevant_info = self.knowledge_skill.get_relevant_sections(normalized_message, top_k=3)
        
        if "No relevant documentation found" in relevant_info:
            base_response = self._generate_no_info_response(message, channel)
        else:
            base_response = self._generate_response(
                message=normalized_message,
                relevant_info=relevant_info,
                channel=channel
            )
        
        response_parts.append(base_response)
        
        return '\n\n'.join(response_parts)
    
    def process_message(self, message: str, channel: str,
                       customer_email: str = None, customer_phone: str = None,
                       subject: str = None) -> AgentResponse:
        """
        Process an incoming customer message.
        
        This is the main entry point for the agent. It follows these steps:
        1. Receive and validate input
        2. Normalize message
        3. Identify customer
        4. Analyze sentiment
        5. Search knowledge base
        6. Generate response
        7. Check for escalation
        8. Format for channel
        9. Return structured result
        
        Args:
            message: Customer message text.
            channel: Channel type ('email', 'whatsapp', 'web_form').
            customer_email: Customer email address (for email/web_form).
            customer_phone: Customer phone number (for whatsapp).
            subject: Optional subject line (for email/web_form).
            
        Returns:
            AgentResponse with formatted response and metadata.
        """
        start_time = time.time()
        
        try:
            # STEP 1: Validate input
            channel = channel.lower()
            if channel not in self.channels:
                raise ValueError(f"Unknown channel: {channel}. Must be one of: email, whatsapp, web_form")
            
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")
            
            # STEP 2: Normalize message
            normalized_message = self._normalize_message(message)
            
            # STEP 3: Identify customer
            customer_info = self.customer_skill.identify(
                email=customer_email,
                phone=customer_phone
            )
            
            # STEP 4: Analyze sentiment
            sentiment_result = self.sentiment_skill.analyze(normalized_message)
            sentiment_score = sentiment_result['score']
            
            # STEP 5: Check for immediate escalation BEFORE generating response
            # (e.g., human agent request, refund request)
            escalation_check = self.escalation_skill.should_escalate(
                normalized_message, sentiment_score
            )
            
            # If immediate escalation needed, skip response generation
            if escalation_check['escalate']:
                response_text = self._generate_escalation_response(
                    channel, escalation_check['reason']
                )
            else:
                # STEP 6: Search knowledge base
                relevant_info = self.knowledge_skill.get_relevant_sections(
                    normalized_message, top_k=3
                )
                
                # STEP 7: Generate response
                response_text = self._generate_response(
                    message=normalized_message,
                    relevant_info=relevant_info,
                    channel=channel,
                    customer_name=customer_info.get('customer_info', {}).get('name') if customer_info.get('customer_info') else None
                )
            
            # STEP 8: Format for channel
            formatted_response = self.channel_skill.format_response(
                response_text, channel,
                customer_name=customer_info.get('customer_info', {}).get('name') if customer_info.get('customer_info') else None
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # STEP 9: Return structured result
            return AgentResponse(
                response_text=formatted_response,
                should_escalate=escalation_check['escalate'],
                escalation_reason=escalation_check['reason'],
                sentiment_score=sentiment_score,
                channel_used=channel,
                customer_id=customer_info['customer_id'],
                is_new_customer=customer_info['is_new_customer'],
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            # Handle any errors gracefully
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            error_response = self._generate_error_response(channel, str(e))
            
            return AgentResponse(
                response_text=error_response,
                should_escalate=True,
                escalation_reason=f"Error processing message: {str(e)}",
                sentiment_score=0.5,
                channel_used=channel,
                processing_time_ms=processing_time_ms
            )
    
    def _normalize_message(self, message: str) -> str:
        """
        Clean and normalize a message regardless of channel.
        
        - Removes extra whitespace
        - Normalizes case for processing
        - Preserves original for response generation
        
        Args:
            message: Raw message text.
            
        Returns:
            Normalized message text.
        """
        # Remove extra whitespace
        normalized = ' '.join(message.split())
        
        # Fix common typos (could be expanded)
        typo_fixes = {
            'cant': "can't",
            'dont': "don't",
            'wont': "won't",
            'didnt': "didn't",
            'doesnt': "doesn't"
        }
        
        words = normalized.lower().split()
        fixed_words = [typo_fixes.get(word, word) for word in words]
        
        return ' '.join(fixed_words)
    
    def _generate_response(self, message: str, relevant_info: str,
                          channel: str, customer_name: str = None) -> str:
        """
        Generate a helpful response based on found information.
        
        Args:
            message: Customer message (normalized).
            relevant_info: Relevant documentation sections.
            channel: Channel type for tone adjustment.
            customer_name: Optional customer name.
            
        Returns:
            Generated response text.
        """
        # Check if no relevant info found
        if "No relevant documentation found" in relevant_info:
            return self._generate_no_info_response(message, channel)
        
        # Build response based on relevant info
        response_parts = []
        
        # Acknowledge the issue
        response_parts.append(self._get_acknowledgment(message, channel))
        
        # Provide the solution from docs
        response_parts.append(relevant_info)
        
        # Add offer for further help
        response_parts.append(self._get_closing(channel))
        
        return '\n\n'.join(response_parts)
    
    def _get_acknowledgment(self, message: str, channel: str) -> str:
        """
        Get an appropriate acknowledgment based on message and channel.
        
        Args:
            message: Customer message.
            channel: Channel type.
            
        Returns:
            Acknowledgment text.
        """
        message_lower = message.lower()
        
        # Detect issue type
        if 'login' in message_lower or 'password' in message_lower:
            ack = "I understand you're having trouble logging in."
        elif 'not working' in message_lower or 'broken' in message_lower:
            ack = "I'm sorry to hear you're experiencing issues."
        elif 'how' in message_lower or 'help' in message_lower:
            ack = "I'd be happy to help you with that."
        elif 'price' in message_lower or 'plan' in message_lower:
            ack = "I can provide information about our plans."
        else:
            ack = "Thank you for reaching out to us."
        
        return ack
    
    def _get_closing(self, channel: str) -> str:
        """
        Get an appropriate closing based on channel.
        
        Args:
            channel: Channel type.
            
        Returns:
            Closing text.
        """
        if channel == 'email':
            return "Please let us know if you need any further assistance."
        elif channel == 'whatsapp':
            return "Let me know if you need more help!"
        else:  # web_form
            return "Feel free to reach out if you have any other questions."
    
    def _generate_no_info_response(self, message: str, channel: str) -> str:
        """
        Generate response when no relevant documentation is found.
        
        Args:
            message: Customer message.
            channel: Channel type.
            
        Returns:
            Response indicating need for escalation.
        """
        if channel == 'whatsapp':
            return "Let me look into this for you. I'll connect you with a specialist who can help."
        elif channel == 'email':
            return """Thank you for your message. Your query requires specialized assistance. 
I'm escalating this to our technical team who will get back to you shortly."""
        else:
            return """Thank you for contacting us. Your question requires assistance from 
our specialized team. We're escalating your ticket and someone will be in touch soon."""
    
    def _generate_escalation_response(self, channel: str, reason: str) -> str:
        """
        Generate response for escalated tickets.
        
        Args:
            channel: Channel type.
            reason: Reason for escalation.
            
        Returns:
            Escalation acknowledgment response.
        """
        if channel == 'whatsapp':
            return "I understand your concern. Let me connect you with a human agent who can better assist you."
        elif channel == 'email':
            return """Thank you for bringing this to our attention. Your message has been 
escalated to our specialist team. A team member will contact you within 24 hours."""
        else:
            return """Your request has been escalated to our specialist team. 
We will contact you via email within 24 hours with a resolution."""
    
    def _generate_error_response(self, channel: str, error: str) -> str:
        """
        Generate error response.
        
        Args:
            channel: Channel type.
            error: Error message.
            
        Returns:
            Error response text.
        """
        if channel == 'whatsapp':
            return "Sorry, I encountered an issue. Let me connect you to a human agent."
        else:
            return """We apologize, but we encountered an issue processing your request. 
Your ticket has been escalated to our technical team for assistance."""


def process_ticket(agent: CustomerSuccessAgent, ticket: Dict) -> AgentResponse:
    """
    Process a single ticket through the agent.
    
    Args:
        agent: CustomerSuccessAgent instance.
        ticket: Ticket dictionary from sample-tickets.json.
        
    Returns:
        AgentResponse from processing the ticket.
    """
    channel = ticket['channel']
    message = ticket['message']
    from_field = ticket['from']
    subject = ticket.get('subject', None)
    
    # Determine email vs phone
    customer_email = from_field if '@' in from_field else None
    customer_phone = from_field if '@' not in from_field else None
    
    return agent.process_message(
        message=message,
        channel=channel,
        customer_email=customer_email,
        customer_phone=customer_phone,
        subject=subject
    )


def main():
    """Main function to demonstrate the agent with sample tickets."""
    print("=" * 60)
    print("TechCorp Customer Success AI Agent - Prototype Demo")
    print("=" * 60)
    
    # Initialize agent
    agent = CustomerSuccessAgent()
    
    # Load sample tickets
    tickets_path = Path(__file__).parent.parent.parent / "context" / "sample-tickets.json"
    
    with open(tickets_path, 'r', encoding='utf-8') as f:
        tickets = json.load(f)
    
    print(f"\nProcessing {len(tickets)} sample tickets...\n")
    
    results = []
    
    for ticket in tickets:
        print("-" * 60)
        print(f"Ticket #{ticket['id']} | Channel: {ticket['channel'].upper()}")
        print(f"From: {ticket['from']}")
        print(f"Message: {ticket['message']}")
        print(f"Expected Action: {ticket['expected_action']}")
        print()
        
        # Process ticket
        response = process_ticket(agent, ticket)
        results.append((ticket, response))
        
        # Display results
        print(f"Sentiment Score: {response.sentiment_score:.2f} ({'positive' if response.sentiment_score >= 0.6 else 'negative' if response.sentiment_score <= 0.4 else 'neutral'})")
        print(f"Should Escalate: {response.should_escalate}")
        if response.escalation_reason:
            print(f"Escalation Reason: {response.escalation_reason}")
        print(f"Customer ID: {response.customer_id}")
        print(f"New Customer: {response.is_new_customer}")
        print(f"Processing Time: {response.processing_time_ms}ms")
        print()
        print("Generated Response:")
        print(response.response_text)
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    escalation_count = sum(1 for _, r in results if r.should_escalate)
    avg_sentiment = sum(r.sentiment_score for _, r in results) / len(results)
    avg_time = sum(r.processing_time_ms for _, r in results) / len(results)
    
    print(f"Total Tickets: {len(results)}")
    print(f"Escalations: {escalation_count} ({escalation_count/len(results)*100:.1f}%)")
    print(f"Average Sentiment: {avg_sentiment:.2f}")
    print(f"Average Processing Time: {avg_time:.1f}ms")
    
    return results


if __name__ == "__main__":
    main()
