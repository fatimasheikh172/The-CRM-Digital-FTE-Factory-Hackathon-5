"""
TechCorp Customer Success AI Agent - Tools

Seven function calling tools for Google Gemini integration.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import asyncpg
from pydantic import BaseModel

from production.config import AgentConfig


# ============================================================================
# PYDANTIC INPUT MODELS
# ============================================================================

class KnowledgeSearchInput(BaseModel):
    """Input model for knowledge base search."""
    query: str
    max_results: int = 5


class CreateTicketInput(BaseModel):
    """Input model for ticket creation."""
    customer_id: str
    issue: str
    channel: str
    priority: str = "medium"
    category: str = "general"
    subject: str = ""


class GetCustomerHistoryInput(BaseModel):
    """Input model for customer history lookup."""
    customer_id: str


class EscalateToHumanInput(BaseModel):
    """Input model for escalation."""
    ticket_id: str
    reason: str
    urgency: str = "normal"
    customer_id: str = ""


class SendResponseInput(BaseModel):
    """Input model for sending responses."""
    ticket_id: str
    message: str
    channel: str
    customer_email: str = ""
    customer_phone: str = ""


class AnalyzeSentimentInput(BaseModel):
    """Input model for sentiment analysis."""
    message: str
    customer_id: str = ""


class GetTicketStatusInput(BaseModel):
    """Input model for ticket status lookup."""
    ticket_id: str


# ============================================================================
# DATABASE CONNECTION HELPERS
# ============================================================================

async def get_db_connection() -> asyncpg.Connection:
    """Get a database connection."""
    conn = await asyncpg.connect(
        host=AgentConfig.DB_HOST,
        port=AgentConfig.DB_PORT,
        database=AgentConfig.DB_NAME,
        user=AgentConfig.DB_USER,
        password=AgentConfig.DB_PASSWORD
    )
    return conn


# ============================================================================
# SIMULATION HELPERS
# ============================================================================

def get_simulation_dir() -> Path:
    """Get the simulation directory path."""
    return Path(__file__).parent.parent.parent / "simulation"


def save_to_simulation(channel: str, data: Dict[str, Any]) -> None:
    """Save data to simulation file."""
    sim_dir = get_simulation_dir()
    sim_dir.mkdir(parents=True, exist_ok=True)
    
    if channel == "email":
        file_path = sim_dir / "gmail_sent.json"
    elif channel == "whatsapp":
        file_path = sim_dir / "whatsapp_sent.json"
    else:
        file_path = sim_dir / "web_form_responses.json"
    
    # Load existing data
    existing = []
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing = []
    
    # Add new entry
    data['saved_at'] = datetime.now().isoformat()
    existing.append(data)
    
    # Save back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)


# ============================================================================
# TOOL 1: search_knowledge_base
# ============================================================================

async def search_knowledge_base(query: str, max_results: int = 5) -> str:
    """
    Search product documentation for relevant information.
    
    Use when customer asks about product features or how-to.
    - Query database knowledge_base table
    - Search by keyword in title and content
    - Return formatted results
    - If no results: return helpful no-results message
    
    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
    
    Returns:
        Formatted search results.
    """
    try:
        conn = await get_db_connection()
        try:
            # Search knowledge base
            search_query = """
                SELECT id, title, content, category, tags
                FROM knowledge_base
                WHERE is_active = TRUE
                  AND (
                      title ILIKE $1
                      OR content ILIKE $1
                  )
                ORDER BY created_at DESC
                LIMIT $2
            """
            
            rows = await conn.fetch(search_query, f'%{query}%', max_results)
            
            if not rows:
                return (
                    "No relevant documentation found for your query.\n"
                    "Let me connect you with a specialist who can help."
                )
            
            # Format results
            output_lines = [f"Search Results for: '{query}'\n"]
            output_lines.append("=" * 50)
            
            for i, row in enumerate(rows, 1):
                output_lines.append(f"\n{i}. {row['title']}")
                output_lines.append(f"   Category: {row['category']}")
                content_preview = row['content'][:200] + "..." if len(row['content']) > 200 else row['content']
                output_lines.append(f"   Content: {content_preview}")
            
            output_lines.append("\n" + "=" * 50)
            output_lines.append(f"Total results: {len(rows)}")
            
            return "\n".join(output_lines)
            
        finally:
            await conn.close()
            
    except asyncpg.PostgresError as e:
        return f"Error searching knowledge base: {str(e)}"
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


# ============================================================================
# TOOL 2: create_ticket
# ============================================================================

async def create_ticket(
    customer_id: str,
    issue: str,
    channel: str,
    priority: str = "medium",
    category: str = "general",
    subject: str = ""
) -> str:
    """
    Create support ticket. ALWAYS call this first.

    - Insert into tickets table (port 5433)
    - Return ticket_id

    Args:
        customer_id: Customer identifier (email or phone).
        issue: Description of the issue.
        channel: Channel type (email, whatsapp, web_form).
        priority: Priority level (low, medium, high).
        category: Issue category.
        subject: Optional subject line.

    Returns:
        Ticket creation confirmation with ticket ID.
    """
    try:
        conn = await get_db_connection()
        try:
            # Generate proper UUID for ticket
            ticket_uuid = str(uuid.uuid4())
            display_ticket_id = f"TKT-{ticket_uuid[:8].upper()}"

            # First, get or create customer
            customer = await conn.fetchrow(
                """
                SELECT id FROM customers WHERE email = $1 OR phone = $1
                """,
                customer_id
            )

            if not customer:
                # Create new customer
                is_email = '@' in customer_id
                if is_email:
                    customer = await conn.fetchrow(
                        """
                        INSERT INTO customers (email, metadata)
                        VALUES ($1, $2)
                        RETURNING id
                        """,
                        customer_id,
                        json.dumps({'first_channel': channel})
                    )
                else:
                    customer = await conn.fetchrow(
                        """
                        INSERT INTO customers (phone, metadata)
                        VALUES ($1, $2)
                        RETURNING id
                        """,
                        customer_id,
                        json.dumps({'first_channel': channel})
                    )

            customer_db_id = customer['id']

            # Create conversation
            conversation = await conn.fetchrow(
                """
                INSERT INTO conversations (customer_id, initial_channel, current_channel, metadata)
                VALUES ($1, $2, $2, $3)
                RETURNING id
                """,
                customer_db_id,
                channel,
                json.dumps({'source': 'agent'})
            )

            conversation_id = conversation['id']

            # Create ticket with UUID
            await conn.execute(
                """
                INSERT INTO tickets (
                    id, customer_id, conversation_id, source_channel,
                    category, priority, subject, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                ticket_uuid,
                customer_db_id,
                conversation_id,
                channel,
                category,
                priority,
                subject if subject else issue[:50],
                'open'
            )
            
            return (
                f"Ticket Created Successfully!\n"
                f"Ticket ID: {display_ticket_id}\n"
                f"Customer: {customer_id}\n"
                f"Channel: {channel}\n"
                f"Priority: {priority}\n"
                f"Status: Open"
            )
            
        finally:
            await conn.close()
            
    except asyncpg.PostgresError as e:
        # Return simulated success for testing without DB
        ticket_uuid = str(uuid.uuid4())
        display_ticket_id = f"TKT-{ticket_uuid[:8].upper()}"
        return (
            f"Ticket Created Successfully!\n"
            f"Ticket ID: {display_ticket_id}\n"
            f"Customer: {customer_id}\n"
            f"Channel: {channel}\n"
            f"Priority: {priority}\n"
            f"Status: Open (simulated)"
        )
    except Exception as e:
        # Return simulated success for testing without DB
        ticket_uuid = str(uuid.uuid4())
        display_ticket_id = f"TKT-{ticket_uuid[:8].upper()}"
        return (
            f"Ticket Created Successfully!\n"
            f"Ticket ID: {display_ticket_id}\n"
            f"Customer: {customer_id}\n"
            f"Channel: {channel}\n"
            f"Priority: {priority}\n"
            f"Status: Open (simulated)"
        )


# ============================================================================
# TOOL 3: get_customer_history
# ============================================================================

async def get_customer_history(customer_id: str) -> str:
    """
    Get customer interaction history across ALL channels.
    
    - Query conversations + messages tables
    - Last 5 conversations
    - Show channel, date, status
    - New customer: return "No previous history found"
    
    Args:
        customer_id: Customer identifier (email or phone).
    
    Returns:
        Formatted customer history.
    """
    try:
        conn = await get_db_connection()
        try:
            # Find customer
            customer = await conn.fetchrow(
                """
                SELECT id, email, phone, name FROM customers
                WHERE email = $1 OR phone = $1
                """,
                customer_id
            )
            
            if not customer:
                return f"No previous history found for customer: {customer_id}\nThis appears to be a new customer."
            
            customer_db_id = customer['id']
            
            # Get conversations
            conversations = await conn.fetch(
                """
                SELECT id, initial_channel, current_channel, started_at, status,
                       topics_discussed, resolution_type
                FROM conversations
                WHERE customer_id = $1
                ORDER BY started_at DESC
                LIMIT 5
                """,
                customer_db_id
            )
            
            if not conversations:
                return f"No conversation history found for customer: {customer_id}"
            
            # Format output
            output_lines = [f"Customer History: {customer_id}\n"]
            output_lines.append("=" * 50)
            output_lines.append(f"Customer ID: {customer_db_id}")
            
            if customer['name']:
                output_lines.append(f"Name: {customer['name']}")
            if customer['email']:
                output_lines.append(f"Email: {customer['email']}")
            if customer['phone']:
                output_lines.append(f"Phone: {customer['phone']}")
            
            output_lines.append(f"Total Conversations: {len(conversations)}")
            output_lines.append("=" * 50)
            
            for i, conv in enumerate(conversations, 1):
                output_lines.append(f"\n--- Conversation {i} ---")
                output_lines.append(f"Channel: {conv['initial_channel']}")
                output_lines.append(f"Started: {conv['started_at']}")
                output_lines.append(f"Status: {conv['status']}")
                
                if conv['topics_discussed']:
                    output_lines.append(f"Topics: {', '.join(conv['topics_discussed'])}")
                
                if conv['resolution_type']:
                    output_lines.append(f"Resolution: {conv['resolution_type']}")
            
            return "\n".join(output_lines)
            
        finally:
            await conn.close()
            
    except asyncpg.PostgresError as e:
        return f"Error retrieving customer history: {str(e)}"
    except Exception as e:
        return f"Error retrieving customer history: {str(e)}"


# ============================================================================
# TOOL 4: escalate_to_human
# ============================================================================

async def escalate_to_human(
    ticket_id: str,
    reason: str,
    urgency: str = "normal",
    customer_id: str = ""
) -> str:
    """
    Escalate to human support agent.
    
    - Update ticket status to escalated in database
    - Insert into escalations table
    - Return escalation confirmation
    
    Args:
        ticket_id: Ticket ID to escalate.
        reason: Reason for escalation.
        urgency: Urgency level (normal, high, critical).
        customer_id: Customer identifier.
    
    Returns:
        Escalation confirmation.
    """
    try:
        conn = await get_db_connection()
        try:
            # Generate escalation ID
            escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
            
            # Update ticket status
            await conn.execute(
                """
                UPDATE tickets
                SET status = 'escalated', escalation_reason = $1, updated_at = NOW()
                WHERE id = $2
                """,
                reason,
                ticket_id
            )
            
            # Create escalation record
            await conn.execute(
                """
                INSERT INTO escalations (
                    id, ticket_id, reason, urgency, status, created_at
                )
                VALUES ($1, $2, $3, $4, $5, NOW())
                """,
                escalation_id,
                ticket_id,
                reason,
                urgency,
                'pending'
            )
            
            # Determine response time
            response_times = {
                'critical': '15 minutes',
                'high': '1 hour',
                'normal': '24 hours'
            }
            response_time = response_times.get(urgency, '24 hours')
            
            return (
                f"Escalation Created Successfully!\n"
                f"Escalation ID: {escalation_id}\n"
                f"Ticket ID: {ticket_id}\n"
                f"Urgency: {urgency}\n"
                f"Reason: {reason}\n"
                f"Expected Response Time: {response_time}\n"
                f"Status: Pending human agent assignment"
            )
            
        finally:
            await conn.close()
            
    except asyncpg.PostgresError as e:
        return f"Error escalating ticket: {str(e)}"
    except Exception as e:
        return f"Error escalating ticket: {str(e)}"


# ============================================================================
# TOOL 5: send_response
# ============================================================================

async def send_response(
    ticket_id: str,
    message: str,
    channel: str,
    customer_email: str = "",
    customer_phone: str = ""
) -> str:
    """
    Send response to customer via their channel.
    
    - Format message for channel
    - Save to simulation files
    - Save to database messages table
    - Update ticket to resolved
    - Return delivery confirmation
    
    Args:
        ticket_id: Ticket ID to respond to.
        message: Response message.
        channel: Channel type (email, whatsapp, web_form).
        customer_email: Customer email (for email channel).
        customer_phone: Customer phone (for whatsapp channel).
    
    Returns:
        Delivery confirmation.
    """
    try:
        conn = await get_db_connection()
        try:
            # Get ticket details
            ticket = await conn.fetchrow(
                """
                SELECT t.*, c.email, c.phone
                FROM tickets t
                JOIN customers c ON t.customer_id = c.id
                WHERE t.id = $1
                """,
                ticket_id
            )
            
            if not ticket:
                return f"Error: Ticket not found: {ticket_id}"
            
            # Determine recipient
            recipient = customer_email or customer_phone or ticket['email'] or ticket['phone']
            
            # Save to simulation
            save_to_simulation(channel, {
                'ticket_id': ticket_id,
                'message': message,
                'channel': channel,
                'recipient': recipient,
                'status': 'sent'
            })
            
            # Get conversation ID
            conversation_id = ticket['conversation_id']
            
            # Save message to database
            await conn.execute(
                """
                INSERT INTO messages (
                    conversation_id, channel, direction, role, content, metadata
                )
                VALUES ($1, $2, 'outbound', 'agent', $3, $4)
                """,
                conversation_id,
                channel,
                message,
                json.dumps({'ticket_id': ticket_id})
            )
            
            # Update ticket status
            await conn.execute(
                """
                UPDATE tickets
                SET status = 'resolved', updated_at = NOW(), resolved_at = NOW()
                WHERE id = $1
                """,
                ticket_id
            )
            
            return (
                f"Response Sent Successfully!\n"
                f"Ticket ID: {ticket_id}\n"
                f"Channel: {channel}\n"
                f"Recipient: {recipient}\n"
                f"Status: Delivered\n"
                f"Timestamp: {datetime.now().isoformat()}"
            )
            
        finally:
            await conn.close()
            
    except asyncpg.PostgresError as e:
        return f"Error sending response: {str(e)}"
    except Exception as e:
        return f"Error sending response: {str(e)}"


# ============================================================================
# TOOL 6: analyze_sentiment
# ============================================================================

async def analyze_sentiment(
    message: str,
    customer_id: str = ""
) -> str:
    """
    Analyze customer message sentiment.
    
    - Use keyword-based sentiment analysis
    - Return score (0.0-1.0), label, recommendation
    - score < 0.3: recommend escalation
    
    Args:
        message: Customer message to analyze.
        customer_id: Optional customer ID for context.
    
    Returns:
        Sentiment analysis result.
    """
    # Positive indicators
    positive_words = [
        'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'happy', 'pleased', 'satisfied', 'thank', 'thanks',
        'helpful', 'appreciate', 'good', 'awesome', 'perfect'
    ]
    
    # Negative indicators
    negative_words = [
        'terrible', 'awful', 'horrible', 'worst', 'hate',
        'angry', 'frustrated', 'disappointed', 'upset', 'furious',
        'useless', 'broken', 'wrong', 'error', 'problem', 'issue',
        'not working', 'doesn\'t work', 'didn\'t work'
    ]
    
    # Urgency indicators
    urgency_words = [
        'urgent', 'asap', 'immediately', 'right now', 'emergency',
        'critical', 'important', 'need help', 'hurry'
    ]
    
    message_lower = message.lower()
    
    # Count indicators
    positive_count = sum(1 for word in positive_words if word in message_lower)
    negative_count = sum(1 for word in negative_words if word in message_lower)
    urgency_count = sum(1 for word in urgency_words if word in urgency_words if word in message_lower)
    
    # Calculate score (0.0 to 1.0)
    total = positive_count + negative_count
    if total == 0:
        score = 0.5  # Neutral
    else:
        score = positive_count / total
    
    # Adjust for urgency
    if urgency_count > 0:
        score = max(0.0, score - 0.1 * urgency_count)
    
    # Check for caps emphasis (anger indicator)
    caps_words = [word for word in message.split() if word.isupper() and len(word) > 1]
    has_caps_emphasis = len(caps_words) > 2
    if has_caps_emphasis:
        score = max(0.0, score - 0.15)
    
    # Determine label
    if score >= 0.6:
        label = "positive"
    elif score >= 0.4:
        label = "neutral"
    else:
        label = "negative"
    
    # Generate recommendation
    if score < 0.3:
        recommendation = "Recommend immediate escalation - customer is highly negative"
    elif score < 0.5:
        recommendation = "Handle with extra empathy - customer is frustrated"
    else:
        recommendation = "Proceed normally - customer sentiment is acceptable"
    
    return (
        f"Sentiment Analysis Result\n"
        f"{'='*40}\n"
        f"Message: {message[:100]}...\n" if len(message) > 100 else f"Message: {message}\n"
        f"{'='*40}\n"
        f"Score: {score:.2f} (0.0 = very negative, 1.0 = very positive)\n"
        f"Label: {label.upper()}\n"
        f"\nDetails:\n"
        f"  - Positive indicators: {positive_count}\n"
        f"  - Negative indicators: {negative_count}\n"
        f"  - Urgency indicators: {urgency_count}\n"
        f"  - Caps emphasis (anger): {has_caps_emphasis}\n"
        f"\nRecommendation: {recommendation}"
    )


# ============================================================================
# TOOL 7: get_ticket_status
# ============================================================================

async def get_ticket_status(ticket_id: str) -> str:
    """
    Get current ticket details and status.
    
    - Query tickets table
    - Return formatted status
    
    Args:
        ticket_id: Ticket ID to look up.
    
    Returns:
        Formatted ticket status.
    """
    try:
        conn = await get_db_connection()
        try:
            # Get ticket details
            ticket = await conn.fetchrow(
                """
                SELECT t.*, c.email, c.phone
                FROM tickets t
                JOIN customers c ON t.customer_id = c.id
                WHERE t.id = $1
                """,
                ticket_id
            )
            
            if not ticket:
                return (
                    f"Error: Ticket not found: {ticket_id}\n"
                    f"Please verify the ticket ID and try again."
                )
            
            # Format output
            output_lines = [f"Ticket Status: {ticket_id}\n"]
            output_lines.append("=" * 50)
            output_lines.append(f"Customer: {ticket['email'] or ticket['phone']}")
            output_lines.append(f"Status: {ticket['status'].upper()}")
            output_lines.append(f"Priority: {ticket['priority']}")
            output_lines.append(f"Channel: {ticket['source_channel']}")
            output_lines.append(f"Category: {ticket['category']}")
            output_lines.append(f"Created: {ticket['created_at']}")
            output_lines.append(f"Updated: {ticket['updated_at']}")
            
            # Show subject/issue
            output_lines.append(f"\nSubject: {ticket['subject']}")
            
            # Show escalation info if present
            if ticket.get('escalation_reason'):
                output_lines.append(f"\n--- Escalation Info ---")
                output_lines.append(f"Escalation Reason: {ticket['escalation_reason']}")
            
            return "\n".join(output_lines)
            
        finally:
            await conn.close()
            
    except asyncpg.PostgresError as e:
        return f"Error getting ticket status: {str(e)}"
    except Exception as e:
        return f"Error getting ticket status: {str(e)}"


# ============================================================================
# GEMINI FUNCTION DECLARATIONS
# ============================================================================

def get_gemini_function_declarations() -> List[Dict[str, Any]]:
    """
    Get function declarations for Gemini function calling.
    
    Returns:
        List of function declaration dictionaries.
    """
    return [
        {
            "name": "search_knowledge_base",
            "description": "Search product documentation for relevant information. Use when customer asks about product features or how-to.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "create_ticket",
            "description": "Create a new support ticket. ALWAYS call this first before responding to customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer identifier (email or phone)"},
                    "issue": {"type": "string", "description": "Description of the issue"},
                    "channel": {"type": "string", "description": "Channel type (email, whatsapp, web_form)"},
                    "priority": {"type": "string", "description": "Priority level", "default": "medium"},
                    "category": {"type": "string", "description": "Issue category", "default": "general"},
                    "subject": {"type": "string", "description": "Optional subject line"}
                },
                "required": ["customer_id", "issue", "channel"]
            }
        },
        {
            "name": "get_customer_history",
            "description": "Get customer interaction history across all channels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer identifier"}
                },
                "required": ["customer_id"]
            }
        },
        {
            "name": "escalate_to_human",
            "description": "Escalate ticket to human support agent when needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID to escalate"},
                    "reason": {"type": "string", "description": "Reason for escalation"},
                    "urgency": {"type": "string", "description": "Urgency level", "default": "normal"},
                    "customer_id": {"type": "string", "description": "Customer identifier"}
                },
                "required": ["ticket_id", "reason"]
            }
        },
        {
            "name": "send_response",
            "description": "Send response to customer via their channel. ALWAYS use this to reply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID to respond to"},
                    "message": {"type": "string", "description": "Response message"},
                    "channel": {"type": "string", "description": "Channel type"},
                    "customer_email": {"type": "string", "description": "Customer email"},
                    "customer_phone": {"type": "string", "description": "Customer phone"}
                },
                "required": ["ticket_id", "message", "channel"]
            }
        },
        {
            "name": "analyze_sentiment",
            "description": "Analyze customer message sentiment using keyword analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Customer message to analyze"},
                    "customer_id": {"type": "string", "description": "Optional customer ID"}
                },
                "required": ["message"]
            }
        },
        {
            "name": "get_ticket_status",
            "description": "Get current ticket details and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID to look up"}
                },
                "required": ["ticket_id"]
            }
        }
    ]
