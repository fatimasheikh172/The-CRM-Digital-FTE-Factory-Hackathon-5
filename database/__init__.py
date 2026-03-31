"""
Database Module for TechCorp Customer Success AI Agent.

Provides PostgreSQL connectivity with asyncpg connection pooling.
"""

from database.connection import (
    initialize_db,
    get_db_pool,
    close_db_pool,
    check_db_health,
    get_db_connection,
    DatabaseConnection
)

from database.queries import (
    # Customer queries
    create_customer,
    find_customer_by_email,
    find_customer_by_phone,
    get_or_create_customer,
    get_customer_history,
    add_customer_identifier,
    
    # Conversation queries
    create_conversation,
    get_active_conversation,
    update_conversation_status,
    update_conversation_sentiment,
    add_conversation_topic,
    
    # Message queries
    save_message,
    get_conversation_messages,
    get_recent_messages,
    
    # Ticket queries
    create_ticket,
    update_ticket_status,
    get_ticket_by_id,
    get_customer_tickets,
    assign_ticket,
    
    # Knowledge Base queries
    search_knowledge_base,
    get_kb_by_category,
    seed_knowledge_base,
    increment_kb_view_count,
    
    # Metrics queries
    record_metric,
    get_metrics_by_channel,
    get_escalation_rate,
    get_average_response_time,
    get_average_sentiment,
    
    # Escalation queries
    create_escalation,
    resolve_escalation,
    get_pending_escalations
)

__all__ = [
    # Connection
    'initialize_db',
    'get_db_pool',
    'close_db_pool',
    'check_db_health',
    'get_db_connection',
    'DatabaseConnection',
    
    # Customer
    'create_customer',
    'find_customer_by_email',
    'find_customer_by_phone',
    'get_or_create_customer',
    'get_customer_history',
    'add_customer_identifier',
    
    # Conversation
    'create_conversation',
    'get_active_conversation',
    'update_conversation_status',
    'update_conversation_sentiment',
    'add_conversation_topic',
    
    # Message
    'save_message',
    'get_conversation_messages',
    'get_recent_messages',
    
    # Ticket
    'create_ticket',
    'update_ticket_status',
    'get_ticket_by_id',
    'get_customer_tickets',
    'assign_ticket',
    
    # Knowledge Base
    'search_knowledge_base',
    'get_kb_by_category',
    'seed_knowledge_base',
    'increment_kb_view_count',
    
    # Metrics
    'record_metric',
    'get_metrics_by_channel',
    'get_escalation_rate',
    'get_average_response_time',
    'get_average_sentiment',
    
    # Escalation
    'create_escalation',
    'resolve_escalation',
    'get_pending_escalations'
]
