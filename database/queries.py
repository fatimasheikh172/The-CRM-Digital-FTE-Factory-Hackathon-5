"""
Database Queries Module for TechCorp Customer Success AI Agent.

Contains all database query functions organized by entity:
- Customer queries
- Conversation queries
- Message queries
- Ticket queries
- Knowledge Base queries
- Metrics queries

All functions are async and use the connection pool from connection.py
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import asyncpg

from database.connection import get_db_connection, get_db_pool

logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOMER QUERIES
# ============================================================================

async def create_customer(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Create a new customer record.
    
    Args:
        email: Customer email address.
        phone: Customer phone number.
        name: Customer name.
        metadata: Additional metadata as dictionary.
        
    Returns:
        Customer dictionary or None if failed.
    """
    query = """
        INSERT INTO customers (email, phone, name, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING id, email, phone, name, created_at, updated_at, metadata
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                query,
                email,
                phone,
                name,
                json.dumps(metadata) if metadata else '{}'
            )
            
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error creating customer: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating customer: {e}")
        return None


async def find_customer_by_email(email: str) -> Optional[Dict]:
    """
    Find a customer by email address.
    
    Args:
        email: Email address to search for.
        
    Returns:
        Customer dictionary or None if not found.
    """
    query = """
        SELECT id, email, phone, name, created_at, updated_at, metadata
        FROM customers
        WHERE email = $1
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(query, email)
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error finding customer by email: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error finding customer by email: {e}")
        return None


async def find_customer_by_phone(phone: str) -> Optional[Dict]:
    """
    Find a customer by phone number.
    
    Args:
        phone: Phone number to search for.
        
    Returns:
        Customer dictionary or None if not found.
    """
    query = """
        SELECT id, email, phone, name, created_at, updated_at, metadata
        FROM customers
        WHERE phone = $1
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(query, phone)
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error finding customer by phone: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error finding customer by phone: {e}")
        return None


async def get_or_create_customer(identifier: str, channel: str) -> Optional[Dict]:
    """
    Get existing customer by identifier or create new one.
    
    Args:
        identifier: Email or phone number.
        channel: Channel of contact (for metadata).
        
    Returns:
        Customer dictionary.
    """
    is_email = '@' in identifier
    
    # Try to find existing customer
    if is_email:
        customer = await find_customer_by_email(identifier)
    else:
        customer = await find_customer_by_phone(identifier)
    
    if customer:
        return customer
    
    # Create new customer
    if is_email:
        return await create_customer(email=identifier, metadata={'first_channel': channel})
    else:
        return await create_customer(phone=identifier, metadata={'first_channel': channel})


async def get_customer_history(customer_id: str) -> List[Dict]:
    """
    Get all conversations for a customer.
    
    Args:
        customer_id: Customer UUID.
        
    Returns:
        List of conversation dictionaries.
    """
    query = """
        SELECT id, customer_id, initial_channel, current_channel, 
               started_at, ended_at, status, sentiment_score, 
               sentiment_trend, resolution_type, escalated_to,
               topics_discussed, metadata
        FROM conversations
        WHERE customer_id = $1
        ORDER BY started_at DESC
    """
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(query, customer_id)
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting customer history: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting customer history: {e}")
        return []


async def add_customer_identifier(
    customer_id: str,
    identifier_type: str,
    identifier_value: str,
    verified: bool = False
) -> Optional[Dict]:
    """
    Add an additional identifier for a customer.
    
    Args:
        customer_id: Customer UUID.
        identifier_type: Type of identifier (email, phone, social_id, etc.).
        identifier_value: The identifier value.
        verified: Whether the identifier is verified.
        
    Returns:
        Identifier record or None if failed.
    """
    query = """
        INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value, verified)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (identifier_type, identifier_value) DO UPDATE
        SET verified = EXCLUDED.verified
        RETURNING id, customer_id, identifier_type, identifier_value, verified, created_at
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                query, customer_id, identifier_type, identifier_value, verified
            )
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error adding customer identifier: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error adding customer identifier: {e}")
        return None


# ============================================================================
# CONVERSATION QUERIES
# ============================================================================

async def create_conversation(
    customer_id: str,
    channel: str,
    metadata: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Create a new conversation.
    
    Args:
        customer_id: Customer UUID.
        channel: Initial channel (email, whatsapp, web_form).
        metadata: Additional metadata.
        
    Returns:
        Conversation dictionary or None if failed.
    """
    query = """
        INSERT INTO conversations (customer_id, initial_channel, current_channel, metadata)
        VALUES ($1, $2, $2, $3)
        RETURNING id, customer_id, initial_channel, current_channel, 
                  started_at, status, sentiment_trend, metadata
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                query, customer_id, channel, json.dumps(metadata) if metadata else '{}'
            )
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error creating conversation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating conversation: {e}")
        return None


async def get_active_conversation(customer_id: str) -> Optional[Dict]:
    """
    Get the active conversation for a customer.
    
    Args:
        customer_id: Customer UUID.
        
    Returns:
        Conversation dictionary or None if not found.
    """
    query = """
        SELECT id, customer_id, initial_channel, current_channel,
               started_at, status, sentiment_score, sentiment_trend,
               topics_discussed, metadata
        FROM conversations
        WHERE customer_id = $1 AND status = 'active'
        ORDER BY started_at DESC
        LIMIT 1
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(query, customer_id)
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting active conversation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting active conversation: {e}")
        return None


async def update_conversation_status(
    conversation_id: str,
    status: str,
    ended_at: Optional[bool] = False
) -> bool:
    """
    Update conversation status.
    
    Args:
        conversation_id: Conversation UUID.
        status: New status (active, resolved, escalated, pending).
        ended_at: If True, set ended_at to now.
        
    Returns:
        True if updated successfully.
    """
    if ended_at:
        query = """
            UPDATE conversations
            SET status = $1, ended_at = NOW(), updated_at = NOW()
            WHERE id = $2
        """
    else:
        query = """
            UPDATE conversations
            SET status = $1, updated_at = NOW()
            WHERE id = $2
        """
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, status, conversation_id)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error updating conversation status: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating conversation status: {e}")
        return False


async def update_conversation_sentiment(
    conversation_id: str,
    score: float,
    trend: str = 'stable'
) -> bool:
    """
    Update conversation sentiment.
    
    Args:
        conversation_id: Conversation UUID.
        score: Sentiment score (0.0-1.0).
        trend: Sentiment trend (improving, declining, stable).
        
    Returns:
        True if updated successfully.
    """
    query = """
        UPDATE conversations
        SET sentiment_score = $1, sentiment_trend = $2, updated_at = NOW()
        WHERE id = $3
    """
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, score, trend, conversation_id)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error updating conversation sentiment: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating conversation sentiment: {e}")
        return False


async def add_conversation_topic(conversation_id: str, topic: str) -> bool:
    """
    Add a topic to the conversation's topics_discussed array.
    
    Args:
        conversation_id: Conversation UUID.
        topic: Topic to add.
        
    Returns:
        True if updated successfully.
    """
    query = """
        UPDATE conversations
        SET topics_discussed = array_append(
                COALESCE(topics_discussed, ARRAY[]::TEXT[]), 
                $1
            ),
            updated_at = NOW()
        WHERE id = $2
    """
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, topic, conversation_id)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error adding conversation topic: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding conversation topic: {e}")
        return False


# ============================================================================
# MESSAGE QUERIES
# ============================================================================

async def save_message(
    conversation_id: str,
    channel: str,
    direction: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None,
    tokens_used: int = 0,
    latency_ms: int = 0,
    tool_calls: Optional[List] = None,
    sentiment_score: Optional[float] = None
) -> Optional[Dict]:
    """
    Save a message to the database.
    
    Args:
        conversation_id: Conversation UUID.
        channel: Channel type (email, whatsapp, web_form).
        direction: Message direction (inbound, outbound).
        role: Message role (customer, agent).
        content: Message content.
        metadata: Additional metadata.
        tokens_used: Number of tokens used (for LLM calls).
        latency_ms: Latency in milliseconds.
        tool_calls: List of tool calls made.
        sentiment_score: Sentiment score of the message.
        
    Returns:
        Message dictionary or None if failed.
    """
    query = """
        INSERT INTO messages (
            conversation_id, channel, direction, role, content,
            metadata, tokens_used, latency_ms, tool_calls, sentiment_score
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id, conversation_id, channel, direction, role, content,
                  created_at, tokens_used, latency_ms, sentiment_score
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                query,
                conversation_id,
                channel,
                direction,
                role,
                content,
                json.dumps(metadata) if metadata else '{}',
                tokens_used,
                latency_ms,
                json.dumps(tool_calls) if tool_calls else '[]',
                sentiment_score
            )
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error saving message: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving message: {e}")
        return None


async def get_conversation_messages(conversation_id: str) -> List[Dict]:
    """
    Get all messages for a conversation.
    
    Args:
        conversation_id: Conversation UUID.
        
    Returns:
        List of message dictionaries.
    """
    query = """
        SELECT id, conversation_id, channel, direction, role, content,
               created_at, tokens_used, latency_ms, tool_calls,
               sentiment_score, metadata
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
    """
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(query, conversation_id)
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting conversation messages: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting conversation messages: {e}")
        return []


async def get_recent_messages(conversation_id: str, limit: int = 10) -> List[Dict]:
    """
    Get the most recent messages for a conversation.
    
    Args:
        conversation_id: Conversation UUID.
        limit: Maximum number of messages to return.
        
    Returns:
        List of message dictionaries.
    """
    query = """
        SELECT id, conversation_id, channel, direction, role, content,
               created_at, tokens_used, latency_ms, sentiment_score
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(query, conversation_id, limit)
            # Reverse to get chronological order
            messages = [dict(row) for row in rows]
            return list(reversed(messages))
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting recent messages: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting recent messages: {e}")
        return []


# ============================================================================
# TICKET QUERIES
# ============================================================================

async def create_ticket(
    customer_id: str,
    conversation_id: str,
    channel: str,
    category: Optional[str] = None,
    priority: str = 'medium',
    subject: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Create a new support ticket.
    
    Args:
        customer_id: Customer UUID.
        conversation_id: Related conversation UUID.
        channel: Source channel.
        category: Ticket category.
        priority: Priority level (low, medium, high).
        subject: Ticket subject.
        metadata: Additional metadata.
        
    Returns:
        Ticket dictionary or None if failed.
    """
    query = """
        INSERT INTO tickets (
            customer_id, conversation_id, source_channel, category,
            priority, subject, metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, customer_id, conversation_id, source_channel,
                  category, priority, status, subject, created_at
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                query,
                customer_id,
                conversation_id,
                channel,
                category,
                priority,
                subject,
                json.dumps(metadata) if metadata else '{}'
            )
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error creating ticket: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating ticket: {e}")
        return None


async def update_ticket_status(
    ticket_id: str,
    status: str,
    notes: Optional[str] = None
) -> bool:
    """
    Update ticket status.
    
    Args:
        ticket_id: Ticket UUID.
        status: New status (open, in_progress, resolved, closed).
        notes: Optional resolution notes.
        
    Returns:
        True if updated successfully.
    """
    if notes and status == 'resolved':
        query = """
            UPDATE tickets
            SET status = $1, resolution_notes = $2, 
                resolved_at = NOW(), updated_at = NOW()
            WHERE id = $3
        """
        params = (status, notes, ticket_id)
    else:
        query = """
            UPDATE tickets
            SET status = $1, updated_at = NOW()
            WHERE id = $2
        """
        params = (status, ticket_id)
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, *params)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error updating ticket status: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating ticket status: {e}")
        return False


async def get_ticket_by_id(ticket_id: str) -> Optional[Dict]:
    """
    Get a ticket by ID.
    
    Args:
        ticket_id: Ticket UUID.
        
    Returns:
        Ticket dictionary or None if not found.
    """
    query = """
        SELECT id, customer_id, conversation_id, source_channel,
               category, priority, status, subject, created_at,
               updated_at, resolved_at, resolution_notes, escalation_reason,
               assigned_to, metadata
        FROM tickets
        WHERE id = $1
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(query, ticket_id)
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting ticket by ID: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting ticket by ID: {e}")
        return None


async def get_customer_tickets(customer_id: str) -> List[Dict]:
    """
    Get all tickets for a customer.
    
    Args:
        customer_id: Customer UUID.
        
    Returns:
        List of ticket dictionaries.
    """
    query = """
        SELECT id, customer_id, conversation_id, source_channel,
               category, priority, status, subject, created_at,
               updated_at, resolved_at, resolution_notes
        FROM tickets
        WHERE customer_id = $1
        ORDER BY created_at DESC
    """
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(query, customer_id)
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting customer tickets: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting customer tickets: {e}")
        return []


async def assign_ticket(ticket_id: str, assigned_to: str) -> bool:
    """
    Assign a ticket to a human agent.
    
    Args:
        ticket_id: Ticket UUID.
        assigned_to: Agent identifier.
        
    Returns:
        True if updated successfully.
    """
    query = """
        UPDATE tickets
        SET assigned_to = $1, updated_at = NOW()
        WHERE id = $2
    """
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, assigned_to, ticket_id)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error assigning ticket: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error assigning ticket: {e}")
        return False


# ============================================================================
# KNOWLEDGE BASE QUERIES
# ============================================================================

async def search_knowledge_base(
    query: str,
    limit: int = 5,
    category: Optional[str] = None
) -> List[Dict]:
    """
    Search the knowledge base.
    
    Args:
        query: Search query string.
        limit: Maximum results to return.
        category: Optional category filter.
        
    Returns:
        List of matching knowledge base entries.
    """
    if category:
        search_query = """
            SELECT id, title, content, category, tags, created_at, 
                   updated_at, is_active, view_count
            FROM knowledge_base
            WHERE is_active = TRUE
              AND (
                  title ILIKE $1 
                  OR content ILIKE $1
                  OR $1 = ANY(tags)
              )
              AND category = $2
            ORDER BY view_count DESC
            LIMIT $3
        """
        params = (f'%{query}%', category, limit)
    else:
        search_query = """
            SELECT id, title, content, category, tags, created_at,
                   updated_at, is_active, view_count
            FROM knowledge_base
            WHERE is_active = TRUE
              AND (
                  title ILIKE $1 
                  OR content ILIKE $1
                  OR $1 = ANY(tags)
              )
            ORDER BY view_count DESC
            LIMIT $2
        """
        params = (f'%{query}%', limit)
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(search_query, *params)
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Error searching knowledge base: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error searching knowledge base: {e}")
        return []


async def get_kb_by_category(category: str) -> List[Dict]:
    """
    Get knowledge base entries by category.
    
    Args:
        category: Category name.
        
    Returns:
        List of knowledge base entries.
    """
    query = """
        SELECT id, title, content, category, tags, created_at,
               updated_at, is_active, view_count
        FROM knowledge_base
        WHERE category = $1 AND is_active = TRUE
        ORDER BY title ASC
    """
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(query, category)
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting KB by category: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting KB by category: {e}")
        return []


async def seed_knowledge_base(docs_path: str) -> int:
    """
    Seed the knowledge base from product documentation.
    
    Args:
        docs_path: Path to product-docs.md file.
        
    Returns:
        Number of entries inserted.
    """
    try:
        docs_file = Path(docs_path)
        if not docs_file.exists():
            logger.error(f"Docs file not found: {docs_path}")
            return 0
        
        content = docs_file.read_text(encoding='utf-8')
        
        # Split by major sections (## headers)
        sections = content.split('\n## ')
        
        inserted = 0
        for section in sections[1:]:  # Skip first empty section
            lines = section.split('\n')
            title = lines[0].strip()
            
            # Get content (rest of the section)
            section_content = '\n'.join(lines[1:]).strip()
            
            if not title or not section_content:
                continue
            
            # Determine category from title
            category = title.split(':')[0] if ':' in title else 'General'
            
            # Extract tags from content (look for bullet points or keywords)
            tags = [category.lower().replace(' ', '-')]
            
            # Insert into database
            insert_query = """
                INSERT INTO knowledge_base (title, content, category, tags)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
            """
            
            async with get_db_connection() as conn:
                try:
                    await conn.execute(
                        insert_query,
                        title,
                        section_content,
                        category,
                        tags
                    )
                    inserted += 1
                except asyncpg.UniqueViolationError:
                    pass  # Skip duplicates
        
        logger.info(f"Seeded {inserted} knowledge base entries")
        return inserted
        
    except Exception as e:
        logger.error(f"Error seeding knowledge base: {e}")
        return 0


async def increment_kb_view_count(kb_id: str) -> bool:
    """
    Increment the view count for a knowledge base entry.
    
    Args:
        kb_id: Knowledge base entry UUID.
        
    Returns:
        True if updated successfully.
    """
    query = """
        UPDATE knowledge_base
        SET view_count = view_count + 1, updated_at = NOW()
        WHERE id = $1
    """
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, kb_id)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error incrementing KB view count: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error incrementing KB view count: {e}")
        return False


# ============================================================================
# METRICS QUERIES
# ============================================================================

async def record_metric(
    name: str,
    value: float,
    channel: Optional[str] = None,
    dimensions: Optional[Dict] = None
) -> bool:
    """
    Record an agent metric.
    
    Args:
        name: Metric name.
        value: Metric value.
        channel: Optional channel filter.
        dimensions: Additional dimensions as dictionary.
        
    Returns:
        True if recorded successfully.
    """
    query = """
        INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
        VALUES ($1, $2, $3, $4)
    """
    
    try:
        async with get_db_connection() as conn:
            await conn.execute(
                query,
                name,
                value,
                channel,
                json.dumps(dimensions) if dimensions else '{}'
            )
            return True
    except asyncpg.PostgresError as e:
        logger.error(f"Error recording metric: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error recording metric: {e}")
        return False


async def get_metrics_by_channel(hours: int = 24) -> Dict[str, List[Dict]]:
    """
    Get metrics grouped by channel for the last N hours.
    
    Args:
        hours: Number of hours to look back.

    Returns:
        Dictionary with channel as key and list of metrics as value.
    """
    try:
        async with get_db_connection() as conn:
            # Build query with literal interval to avoid parameter type issues
            query = f"""
                SELECT metric_name, metric_value, channel, dimensions, recorded_at
                FROM agent_metrics
                WHERE recorded_at >= NOW() - INTERVAL '{hours} hours'
                ORDER BY channel, recorded_at DESC
            """
            rows = await conn.fetch(query)

            # Group by channel
            metrics_by_channel: Dict[str, List[Dict]] = {}
            for row in rows:
                channel = row['channel'] or 'unknown'
                if channel not in metrics_by_channel:
                    metrics_by_channel[channel] = []
                metrics_by_channel[channel].append(dict(row))

            return metrics_by_channel
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting metrics by channel: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting metrics by channel: {e}")
        return {}


async def get_escalation_rate(hours: int = 24) -> float:
    """
    Calculate the escalation rate for the last N hours.

    Args:
        hours: Number of hours to look back.

    Returns:
        Escalation rate as a float (0.0-1.0).
    """
    try:
        async with get_db_connection() as conn:
            # Build query with literal interval to avoid parameter type issues
            query = f"""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'escalated')::float /
                    NULLIF(COUNT(*), 0) as escalation_rate
                FROM tickets
                WHERE created_at >= NOW() - INTERVAL '{hours} hours'
            """
            row = await conn.fetchrow(query)
            if row and row['escalation_rate'] is not None:
                return float(row['escalation_rate'])
            return 0.0
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting escalation rate: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error getting escalation rate: {e}")
        return 0.0


async def get_average_response_time(hours: int = 24) -> float:
    """
    Get average response time in milliseconds for the last N hours.

    Args:
        hours: Number of hours to look back.

    Returns:
        Average response time in ms.
    """
    try:
        async with get_db_connection() as conn:
            # Build query with literal interval to avoid parameter type issues
            query = f"""
                SELECT AVG(latency_ms) as avg_latency
                FROM messages
                WHERE direction = 'outbound'
                  AND created_at >= NOW() - INTERVAL '{hours} hours'
            """
            row = await conn.fetchrow(query)
            if row and row['avg_latency'] is not None:
                return float(row['avg_latency'])
            return 0.0
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting average response time: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error getting average response time: {e}")
        return 0.0


async def get_average_sentiment(hours: int = 24) -> float:
    """
    Get average customer sentiment score for the last N hours.

    Args:
        hours: Number of hours to look back.

    Returns:
        Average sentiment score (0.0-1.0).
    """
    try:
        async with get_db_connection() as conn:
            # Build query with literal interval to avoid parameter type issues
            query = f"""
                SELECT AVG(sentiment_score) as avg_sentiment
                FROM messages
                WHERE direction = 'inbound'
                  AND role = 'customer'
                  AND created_at >= NOW() - INTERVAL '{hours} hours'
            """
            row = await conn.fetchrow(query)
            if row and row['avg_sentiment'] is not None:
                return float(row['avg_sentiment'])
            return 0.5
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting average sentiment: {e}")
        return 0.5
    except Exception as e:
        logger.error(f"Unexpected error getting average sentiment: {e}")
        return 0.5


# ============================================================================
# ESCALATION QUERIES
# ============================================================================

async def create_escalation(
    ticket_id: str,
    customer_id: str,
    reason: str,
    urgency: str = 'normal',
    notes: Optional[str] = None
) -> Optional[Dict]:
    """
    Create an escalation record.
    
    Args:
        ticket_id: Ticket UUID.
        customer_id: Customer UUID.
        reason: Reason for escalation.
        urgency: Urgency level (normal, high, critical).
        notes: Additional notes.
        
    Returns:
        Escalation dictionary or None if failed.
    """
    query = """
        INSERT INTO escalations (ticket_id, customer_id, reason, urgency, notes)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, ticket_id, customer_id, reason, urgency, status, created_at
    """
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                query, ticket_id, customer_id, reason, urgency, notes
            )
            if row:
                return dict(row)
            return None
    except asyncpg.PostgresError as e:
        logger.error(f"Error creating escalation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating escalation: {e}")
        return None


async def resolve_escalation(
    escalation_id: str,
    resolved_by: str,
    notes: Optional[str] = None
) -> bool:
    """
    Resolve an escalation.
    
    Args:
        escalation_id: Escalation UUID.
        resolved_by: Agent who resolved it.
        notes: Resolution notes.
        
    Returns:
        True if resolved successfully.
    """
    query = """
        UPDATE escalations
        SET status = 'resolved', resolved_at = NOW(),
            resolved_by = $1, notes = COALESCE($2, notes)
        WHERE id = $3
    """
    
    try:
        async with get_db_connection() as conn:
            result = await conn.execute(query, resolved_by, notes, escalation_id)
            return result == 'UPDATE 1'
    except asyncpg.PostgresError as e:
        logger.error(f"Error resolving escalation: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error resolving escalation: {e}")
        return False


async def get_pending_escalations() -> List[Dict]:
    """
    Get all pending escalations.
    
    Returns:
        List of escalation dictionaries.
    """
    query = """
        SELECT e.id, e.ticket_id, e.customer_id, e.reason, e.urgency,
               e.status, e.created_at, t.subject, t.source_channel
        FROM escalations e
        LEFT JOIN tickets t ON e.ticket_id = t.id
        WHERE e.status = 'pending'
        ORDER BY 
            CASE e.urgency
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                ELSE 3
            END,
            e.created_at ASC
    """
    
    try:
        async with get_db_connection() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except asyncpg.PostgresError as e:
        logger.error(f"Error getting pending escalations: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting pending escalations: {e}")
        return []
