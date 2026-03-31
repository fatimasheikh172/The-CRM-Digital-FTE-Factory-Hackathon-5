"""
TechCorp Customer Success MCP Server

This MCP (Model Context Protocol) server exposes the Customer Success AI Agent
capabilities as tools that can be used by external systems.

Available Tools:
1. search_knowledge_base - Search product documentation
2. create_ticket - Create a new support ticket
3. get_customer_history - Get customer conversation history
4. escalate_to_human - Escalate ticket to human agent
5. send_response - Send response via channel
6. analyze_sentiment - Analyze message sentiment
7. get_ticket_status - Get ticket details
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Import skills
from skills.knowledge_retrieval import KnowledgeRetrievalSkill
from skills.sentiment_analysis import SentimentAnalysisSkill
from skills.escalation_decision import EscalationDecisionSkill
from skills.channel_adaptation import ChannelAdaptationSkill
from skills.customer_identification import CustomerIdentificationSkill

# Import memory system
from src.agent.customer_db import CustomerDatabase

# Initialize MCP server
mcp = FastMCP("TechCorp Customer Success Agent")

# Get paths
BASE_DIR = Path(__file__).parent.parent.parent
CONTEXT_DIR = BASE_DIR / "context"
MEMORY_DIR = BASE_DIR / "memory"

# Initialize skills
knowledge_skill = KnowledgeRetrievalSkill(CONTEXT_DIR / "product-docs.md")
sentiment_skill = SentimentAnalysisSkill()
escalation_skill = EscalationDecisionSkill(CONTEXT_DIR / "escalation-rules.md")
channel_skill = ChannelAdaptationSkill(CONTEXT_DIR / "brand-voice.md")
customer_skill = CustomerIdentificationSkill()
customer_db = CustomerDatabase(str(MEMORY_DIR))


# ============================================================================
# Helper Functions
# ============================================================================

def _load_tickets() -> list:
    """Load tickets from JSON file."""
    tickets_file = MEMORY_DIR / "tickets.json"
    try:
        with open(tickets_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_tickets(tickets: list) -> None:
    """Save tickets to JSON file."""
    tickets_file = MEMORY_DIR / "tickets.json"
    with open(tickets_file, 'w', encoding='utf-8') as f:
        json.dump(tickets, f, indent=2)


def _load_escalations() -> list:
    """Load escalations from JSON file."""
    escalations_file = MEMORY_DIR / "escalations.json"
    try:
        with open(escalations_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_escalations(escalations: list) -> None:
    """Save escalations to JSON file."""
    escalations_file = MEMORY_DIR / "escalations.json"
    with open(escalations_file, 'w', encoding='utf-8') as f:
        json.dump(escalations, f, indent=2)


def _get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    """Find a ticket by ID."""
    tickets = _load_tickets()
    for ticket in tickets:
        if ticket.get('ticket_id') == ticket_id:
            return ticket
    return None


def _update_ticket(ticket_id: str, updates: dict) -> bool:
    """Update a ticket with new data."""
    tickets = _load_tickets()
    for i, ticket in enumerate(tickets):
        if ticket.get('ticket_id') == ticket_id:
            tickets[i].update(updates)
            _save_tickets(tickets)
            return True
    return False


# ============================================================================
# TOOL 1: search_knowledge_base
# ============================================================================

@mcp.tool()
def search_knowledge_base(
    query: str,
    max_results: int = 5,
    category: Optional[str] = None
) -> str:
    """
    Search the product knowledge base for relevant information.
    
    Args:
        query: The customer question or search query.
        max_results: Maximum number of results to return (default: 5).
        category: Optional category filter (e.g., "API", "Billing", "Login").
    
    Returns:
        Formatted search results with relevance information.
    """
    try:
        # Search using knowledge retrieval skill
        results = knowledge_skill.search(query)
        
        if not results:
            return (
                "No relevant documentation found for your query.\n"
                "Consider escalating this to a human agent or asking for more details."
            )
        
        # Apply category filter if specified
        if category:
            category_lower = category.lower()
            filtered_results = [
                r for r in results 
                if category_lower in r.get('title', '').lower()
            ]
            if filtered_results:
                results = filtered_results
        
        # Limit results
        results = results[:max_results]
        
        # Format output
        output_lines = [f"Search Results for: '{query}'\n"]
        output_lines.append("=" * 50)
        
        for i, result in enumerate(results, 1):
            output_lines.append(f"\n{i}. {result['title']}")
            output_lines.append(f"   Relevance Score: {result['score']}")
            output_lines.append(f"   Content: {result['content'][:200]}...")
        
        output_lines.append("\n" + "=" * 50)
        output_lines.append(f"Total results: {len(results)}")
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


# ============================================================================
# TOOL 2: create_ticket
# ============================================================================

@mcp.tool()
def create_ticket(
    customer_id: str,
    issue: str,
    priority: str,
    channel: str,
    category: Optional[str] = None
) -> str:
    """
    Create a new support ticket.
    
    Args:
        customer_id: The customer's identifier (email or phone).
        issue: Description of the customer's issue.
        priority: Priority level (low, medium, high).
        channel: Channel source (email, whatsapp, web_form).
        category: Optional category for the ticket.
    
    Returns:
        Ticket ID and confirmation message.
    """
    try:
        # Validate priority
        valid_priorities = ['low', 'medium', 'high']
        if priority.lower() not in valid_priorities:
            return f"Error: Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        
        # Validate channel
        valid_channels = ['email', 'whatsapp', 'web_form']
        if channel.lower() not in valid_channels:
            return f"Error: Invalid channel. Must be one of: {', '.join(valid_channels)}"
        
        # Generate ticket ID
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        # Create ticket record
        ticket = {
            'ticket_id': ticket_id,
            'customer_id': customer_id,
            'issue': issue,
            'priority': priority.lower(),
            'channel': channel.lower(),
            'category': category,
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': [],
            'escalation': None
        }
        
        # Save ticket
        tickets = _load_tickets()
        tickets.append(ticket)
        _save_tickets(tickets)
        
        # Also update customer record
        customer = customer_db.get_or_create_customer(customer_id, channel.lower())
        
        return (
            f"Ticket Created Successfully!\n"
            f"Ticket ID: {ticket_id}\n"
            f"Customer: {customer_id}\n"
            f"Channel: {channel}\n"
            f"Priority: {priority}\n"
            f"Status: Open\n"
            f"Created: {ticket['created_at']}"
        )
        
    except Exception as e:
        return f"Error creating ticket: {str(e)}"


# ============================================================================
# TOOL 3: get_customer_history
# ============================================================================

@mcp.tool()
def get_customer_history(customer_id: str) -> str:
    """
    Get complete conversation history for a customer across all channels.
    
    Args:
        customer_id: The customer's identifier (email or phone).
    
    Returns:
        Formatted conversation history showing all channels and topics.
    """
    try:
        # Find customer in database
        customer = customer_db.get_customer_by_identifier(customer_id)
        
        if not customer:
            return f"No history found for customer: {customer_id}\nThis appears to be a new customer."
        
        # Get conversation history
        history = customer_db.get_customer_history(customer['customer_id'])
        
        if not history:
            return f"No conversation history found for customer: {customer_id}"
        
        # Format output
        output_lines = [f"Customer History: {customer_id}\n"]
        output_lines.append("=" * 50)
        output_lines.append(f"Customer ID: {customer['customer_id']}")
        output_lines.append(f"First Contact: {customer.get('first_contact', 'N/A')}")
        output_lines.append(f"Channels Used: {', '.join(customer.get('channels_used', []))}")
        output_lines.append(f"Total Conversations: {customer.get('total_conversations', 0)}")
        output_lines.append("=" * 50)
        
        for i, conv in enumerate(history, 1):
            conv_data = conv.get('data', {})
            conv_state = conv_data.get('conversation_state', {})
            messages = conv_data.get('messages', [])
            
            output_lines.append(f"\n--- Conversation {i} ---")
            output_lines.append(f"ID: {conv_data.get('conversation_id', 'N/A')}")
            output_lines.append(f"Channel: {conv_state.get('current_channel', 'N/A')}")
            output_lines.append(f"Status: {conv_state.get('status', 'N/A')}")
            output_lines.append(f"Topics: {', '.join(conv_state.get('topics_discussed', [])) or 'None'}")
            output_lines.append(f"Resolution: {conv_state.get('resolution_status', 'N/A')}")
            output_lines.append(f"Messages: {len(messages)}")
            
            # Show recent messages
            if messages:
                output_lines.append("Recent Messages:")
                for msg in messages[-3:]:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:50]
                    output_lines.append(f"  [{role}]: {content}...")
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"Error retrieving customer history: {str(e)}"


# ============================================================================
# TOOL 4: escalate_to_human
# ============================================================================

@mcp.tool()
def escalate_to_human(
    ticket_id: str,
    reason: str,
    urgency: str,
    customer_id: str
) -> str:
    """
    Escalate a ticket to a human agent.
    
    Args:
        ticket_id: The ticket ID to escalate.
        reason: Reason for escalation.
        urgency: Urgency level (normal, high, critical).
        customer_id: The customer's identifier.
    
    Returns:
        Escalation confirmation with escalation ID and next steps.
    """
    try:
        # Validate urgency
        valid_urgencies = ['normal', 'high', 'critical']
        if urgency.lower() not in valid_urgencies:
            return f"Error: Invalid urgency. Must be one of: {', '.join(valid_urgencies)}"
        
        # Find ticket
        ticket = _get_ticket_by_id(ticket_id)
        if not ticket:
            return f"Error: Ticket not found: {ticket_id}"
        
        # Generate escalation ID
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        
        # Create escalation record
        escalation = {
            'escalation_id': escalation_id,
            'ticket_id': ticket_id,
            'customer_id': customer_id,
            'reason': reason,
            'urgency': urgency.lower(),
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'conversation_context': ticket.get('messages', [])
        }
        
        # Save escalation
        escalations = _load_escalations()
        escalations.append(escalation)
        _save_escalations(escalations)
        
        # Update ticket status
        _update_ticket(ticket_id, {
            'status': 'escalated',
            'escalation': {
                'escalation_id': escalation_id,
                'reason': reason,
                'urgency': urgency.lower(),
                'created_at': escalation['created_at']
            },
            'updated_at': datetime.now().isoformat()
        })
        
        # Determine response based on urgency
        if urgency.lower() == 'critical':
            response_time = "15 minutes"
        elif urgency.lower() == 'high':
            response_time = "1 hour"
        else:
            response_time = "24 hours"
        
        return (
            f"Escalation Created Successfully!\n"
            f"Escalation ID: {escalation_id}\n"
            f"Ticket ID: {ticket_id}\n"
            f"Urgency: {urgency}\n"
            f"Reason: {reason}\n"
            f"Expected Response Time: {response_time}\n"
            f"Status: Pending human agent assignment"
        )
        
    except Exception as e:
        return f"Error escalating ticket: {str(e)}"


# ============================================================================
# TOOL 5: send_response
# ============================================================================

@mcp.tool()
def send_response(
    ticket_id: str,
    message: str,
    channel: str
) -> str:
    """
    Send a response to a customer via the specified channel.
    
    Args:
        ticket_id: The ticket ID to respond to.
        message: The response message to send.
        channel: Channel to send via (email, whatsapp, web_form).
    
    Returns:
        Delivery status confirmation.
    """
    try:
        # Validate channel
        valid_channels = ['email', 'whatsapp', 'web_form']
        if channel.lower() not in valid_channels:
            return f"Error: Invalid channel. Must be one of: {', '.join(valid_channels)}"
        
        # Find ticket
        ticket = _get_ticket_by_id(ticket_id)
        if not ticket:
            return f"Error: Ticket not found: {ticket_id}"
        
        # Format message for channel
        formatted_message = channel_skill.format_response(message, channel.lower())
        
        # Simulate sending based on channel
        print(f"\n{'='*50}")
        print(f"SENDING VIA {channel.upper()}")
        print(f"{'='*50}")
        print(formatted_message)
        print(f"{'='*50}\n")
        
        # Save response to ticket
        response_record = {
            'role': 'agent',
            'content': message,
            'channel': channel.lower(),
            'timestamp': datetime.now().isoformat(),
            'sentiment_score': 0.5
        }
        
        tickets = _load_tickets()
        for i, t in enumerate(tickets):
            if t.get('ticket_id') == ticket_id:
                if 'messages' not in t:
                    t['messages'] = []
                t['messages'].append(response_record)
                t['updated_at'] = datetime.now().isoformat()
                break
        _save_tickets(tickets)
        
        return (
            f"Response Sent Successfully!\n"
            f"Ticket ID: {ticket_id}\n"
            f"Channel: {channel}\n"
            f"Status: Delivered\n"
            f"Timestamp: {response_record['timestamp']}"
        )
        
    except Exception as e:
        return f"Error sending response: {str(e)}"


# ============================================================================
# TOOL 6: analyze_sentiment
# ============================================================================

@mcp.tool()
def analyze_sentiment(
    message: str,
    customer_id: Optional[str] = None
) -> str:
    """
    Analyze the sentiment of a customer message.
    
    Args:
        message: The message text to analyze.
        customer_id: Optional customer ID for context.
    
    Returns:
        Sentiment analysis result with score, label, and recommendation.
    """
    try:
        # Analyze sentiment
        result = sentiment_skill.analyze(message)
        
        score = result.get('score', 0.5)
        label = result.get('label', 'neutral')
        details = result.get('details', {})
        
        # Generate recommendation based on score
        if score < 0.3:
            recommendation = "Recommend immediate escalation - customer is highly negative"
        elif score < 0.5:
            recommendation = "Handle with extra empathy - customer is frustrated"
        else:
            recommendation = "Proceed normally - customer sentiment is acceptable"
        
        # Format output
        output = (
            f"Sentiment Analysis Result\n"
            f"{'='*40}\n"
            f"Message: {message[:100]}...\n" if len(message) > 100 else f"Message: {message}\n"
            f"{'='*40}\n"
            f"Score: {score:.2f} (0.0 = very negative, 1.0 = very positive)\n"
            f"Label: {label.upper()}\n"
            f"\nDetails:\n"
            f"  - Positive indicators: {details.get('positive_count', 0)}\n"
            f"  - Negative indicators: {details.get('negative_count', 0)}\n"
            f"  - Urgency indicators: {details.get('urgency_count', 0)}\n"
            f"  - Has negation: {details.get('has_negation', False)}\n"
            f"  - Caps emphasis (anger): {details.get('has_caps_emphasis', False)}\n"
            f"\nRecommendation: {recommendation}"
        )
        
        return output
        
    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"


# ============================================================================
# TOOL 7: get_ticket_status
# ============================================================================

@mcp.tool()
def get_ticket_status(ticket_id: str) -> str:
    """
    Get the current status and details of a ticket.
    
    Args:
        ticket_id: The ticket ID to look up.
    
    Returns:
        Full ticket details including status, channel, priority, and conversation summary.
    """
    try:
        # Find ticket
        ticket = _get_ticket_by_id(ticket_id)
        
        if not ticket:
            return (
                f"Error: Ticket not found: {ticket_id}\n"
                f"Please verify the ticket ID and try again."
            )
        
        # Format output
        output_lines = [f"Ticket Status: {ticket_id}\n"]
        output_lines.append("=" * 50)
        output_lines.append(f"Customer ID: {ticket.get('customer_id', 'N/A')}")
        output_lines.append(f"Status: {ticket.get('status', 'N/A').upper()}")
        output_lines.append(f"Priority: {ticket.get('priority', 'N/A')}")
        output_lines.append(f"Channel: {ticket.get('channel', 'N/A')}")
        output_lines.append(f"Category: {ticket.get('category', 'N/A') or 'None'}")
        output_lines.append(f"Created: {ticket.get('created_at', 'N/A')}")
        output_lines.append(f"Updated: {ticket.get('updated_at', 'N/A')}")
        
        # Show issue
        output_lines.append(f"\nIssue:\n{ticket.get('issue', 'N/A')}")
        
        # Show escalation info if present
        escalation = ticket.get('escalation')
        if escalation:
            output_lines.append("\n--- Escalation Info ---")
            output_lines.append(f"Escalation ID: {escalation.get('escalation_id', 'N/A')}")
            output_lines.append(f"Reason: {escalation.get('reason', 'N/A')}")
            output_lines.append(f"Urgency: {escalation.get('urgency', 'N/A')}")
            output_lines.append(f"Escalated At: {escalation.get('created_at', 'N/A')}")
        
        # Show conversation summary
        messages = ticket.get('messages', [])
        output_lines.append(f"\n--- Conversation Summary ---")
        output_lines.append(f"Total Messages: {len(messages)}")
        
        if messages:
            output_lines.append("\nRecent Messages:")
            for msg in messages[-5:]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:60]
                channel = msg.get('channel', 'N/A')
                timestamp = msg.get('timestamp', 'N/A')[:19]
                output_lines.append(f"  [{timestamp}] [{role}/{channel}]: {content}...")
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"Error getting ticket status: {str(e)}"


# ============================================================================
# MCP Server Runner
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TechCorp Customer Success MCP Server Starting...")
    print("=" * 60)
    print("\nAvailable tools:")
    print("  1. search_knowledge_base")
    print("  2. create_ticket")
    print("  3. get_customer_history")
    print("  4. escalate_to_human")
    print("  5. send_response")
    print("  6. analyze_sentiment")
    print("  7. get_ticket_status")
    print("\n" + "=" * 60)
    print("Server running. Use MCP client to connect.")
    print("=" * 60)
    
    mcp.run()
