"""
Database Tests for TechCorp Customer Success AI Agent.

Simple test file without complex fixtures to avoid asyncio loop issues.
Run with: pytest tests/test_database.py -v
"""

import pytest
import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import queries as db


# ============================================================================
# Helper to get connection parameters
# ============================================================================

def get_connection_params():
    """Get database connection parameters."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5433)),
        'database': os.getenv('DB_NAME', 'fte_db'),
        'user': os.getenv('DB_USER', 'fte_user'),
        'password': os.getenv('DB_PASSWORD', 'fte_password123')
    }


async def clean_db(conn):
    """Clean database."""
    await conn.execute("DELETE FROM escalations")
    await conn.execute("DELETE FROM agent_metrics")
    await conn.execute("DELETE FROM knowledge_base")
    await conn.execute("DELETE FROM messages")
    await conn.execute("DELETE FROM tickets")
    await conn.execute("DELETE FROM conversations")
    await conn.execute("DELETE FROM customer_identifiers")
    await conn.execute("DELETE FROM customers")


# ============================================================================
# TEST 1: Connection Test
# ============================================================================

@pytest.mark.asyncio
async def test_connect_to_postgresql():
    """Test 1.1: Connect to PostgreSQL successfully."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        result = await conn.fetchval('SELECT 1')
        assert result == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_all_tables_exist():
    """Test 1.2: Check all 8 tables exist."""
    expected_tables = [
        'customers',
        'customer_identifiers',
        'conversations',
        'messages',
        'tickets',
        'knowledge_base',
        'agent_metrics',
        'escalations'
    ]

    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        table_names = [row['table_name'] for row in tables]

        for table in expected_tables:
            assert table in table_names, f"Table '{table}' not found"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_all_indexes_exist():
    """Test 1.3: Check all 13 indexes exist."""
    expected_indexes = [
        'idx_customers_email',
        'idx_customers_phone',
        'idx_customer_identifiers_value',
        'idx_conversations_customer',
        'idx_conversations_status',
        'idx_conversations_channel',
        'idx_messages_conversation',
        'idx_messages_channel',
        'idx_tickets_status',
        'idx_tickets_channel',
        'idx_tickets_customer',
        'idx_escalations_ticket',
        'idx_agent_metrics_recorded'
    ]

    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        indexes = await conn.fetch("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """)
        index_names = [row['indexname'] for row in indexes]

        for index in expected_indexes:
            assert index in index_names, f"Index '{index}' not found"
    finally:
        await conn.close()


# ============================================================================
# TEST 2: Customer CRUD
# ============================================================================

@pytest.mark.asyncio
async def test_create_customer():
    """Test 2.1: Create new customer."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(
            email="test@example.com",
            phone="+1234567890",
            name="Test Customer"
        )

        assert customer is not None
        assert customer['email'] == "test@example.com"
        assert customer['phone'] == "+1234567890"
        assert customer['name'] == "Test Customer"
        assert 'id' in customer
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_customer_by_email():
    """Test 2.2: Find customer by email."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        # Create customer
        await db.create_customer(
            email="findme@example.com",
            name="Find Me"
        )

        # Find by email
        customer = await db.find_customer_by_email("findme@example.com")

        assert customer is not None
        assert customer['email'] == "findme@example.com"
        assert customer['name'] == "Find Me"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_find_customer_by_phone():
    """Test 2.3: Find customer by phone."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        # Create customer
        await db.create_customer(
            phone="+9876543210",
            name="Phone Customer"
        )

        # Find by phone
        customer = await db.find_customer_by_phone("+9876543210")

        assert customer is not None
        assert customer['phone'] == "+9876543210"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_or_create_customer():
    """Test 2.4: Get or create customer."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        # First call - should create
        customer1 = await db.get_or_create_customer(
            "newcustomer@example.com",
            "email"
        )

        assert customer1 is not None

        # Second call - should get existing
        customer2 = await db.get_or_create_customer(
            "newcustomer@example.com",
            "email"
        )

        assert customer2 is not None
        assert customer2['id'] == customer1['id']
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_update_customer():
    """Test 2.5: Update customer metadata."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(
            email="update@example.com",
            name="Original Name"
        )

        await conn.execute(
            "UPDATE customers SET name = $1, updated_at = NOW() WHERE id = $2",
            "Updated Name",
            customer['id']
        )

        updated = await db.find_customer_by_email("update@example.com")
        assert updated['name'] == "Updated Name"
    finally:
        await conn.close()


# ============================================================================
# TEST 3: Conversation Flow
# ============================================================================

@pytest.mark.asyncio
async def test_create_conversation():
    """Test 3.1: Create conversation."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="conv@example.com")

        conversation = await db.create_conversation(
            customer_id=customer['id'],
            channel="email"
        )

        assert conversation is not None
        assert conversation['customer_id'] == customer['id']
        assert conversation['initial_channel'] == "email"
        assert conversation['status'] == 'active'
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_add_messages():
    """Test 3.2: Add messages to conversation."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="messages@example.com")
        conversation = await db.create_conversation(
            customer_id=customer['id'],
            channel="whatsapp"
        )

        # Add customer message
        msg1 = await db.save_message(
            conversation_id=conversation['id'],
            channel="whatsapp",
            direction="inbound",
            role="customer",
            content="Hello, I need help",
            sentiment_score=0.5
        )

        # Add agent response
        msg2 = await db.save_message(
            conversation_id=conversation['id'],
            channel="whatsapp",
            direction="outbound",
            role="agent",
            content="How can I help you?",
            latency_ms=150
        )

        assert msg1 is not None
        assert msg2 is not None
        assert msg1['role'] == "customer"
        assert msg2['role'] == "agent"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_update_conversation_status():
    """Test 3.3: Update conversation status."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="status@example.com")
        conversation = await db.create_conversation(
            customer_id=customer['id'],
            channel="email"
        )

        # Update to resolved
        success = await db.update_conversation_status(
            conversation['id'],
            'resolved',
            ended_at=True
        )

        assert success is True

        # Verify status
        row = await conn.fetchrow(
            "SELECT status, ended_at FROM conversations WHERE id = $1",
            conversation['id']
        )
        assert row['status'] == 'resolved'
        assert row['ended_at'] is not None
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_update_conversation_sentiment():
    """Test 3.4: Update conversation sentiment."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="sentiment@example.com")
        conversation = await db.create_conversation(
            customer_id=customer['id'],
            channel="web_form"
        )

        success = await db.update_conversation_sentiment(
            conversation['id'],
            score=0.3,
            trend='declining'
        )

        assert success is True

        row = await conn.fetchrow(
            "SELECT sentiment_score, sentiment_trend FROM conversations WHERE id = $1",
            conversation['id']
        )
        assert float(row['sentiment_score']) == 0.3
        assert row['sentiment_trend'] == 'declining'
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_customer_history():
    """Test 3.5: Get customer conversation history."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="history@example.com")

        # Create multiple conversations
        await db.create_conversation(customer['id'], "email")
        await db.create_conversation(customer['id'], "whatsapp")

        history = await db.get_customer_history(customer['id'])

        assert len(history) == 2
    finally:
        await conn.close()


# ============================================================================
# TEST 4: Ticket Flow
# ============================================================================

@pytest.mark.asyncio
async def test_create_ticket():
    """Test 4.1: Create ticket."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="ticket@example.com")
        conversation = await db.create_conversation(
            customer_id=customer['id'],
            channel="email"
        )

        ticket = await db.create_ticket(
            customer_id=customer['id'],
            conversation_id=conversation['id'],
            channel="email",
            category="Technical",
            priority="high",
            subject="Cannot login to account"
        )

        assert ticket is not None
        assert ticket['customer_id'] == customer['id']
        assert ticket['priority'] == "high"
        assert ticket['status'] == "open"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_update_ticket_status():
    """Test 4.2: Update ticket status."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="ticket2@example.com")
        conversation = await db.create_conversation(customer['id'], "email")
        ticket = await db.create_ticket(
            customer['id'], conversation['id'], "email",
            subject="Test ticket"
        )

        success = await db.update_ticket_status(
            ticket['id'],
            'resolved',
            notes="Issue resolved by resetting password"
        )

        assert success is True

        updated = await db.get_ticket_by_id(ticket['id'])
        assert updated['status'] == 'resolved'
        assert updated['resolution_notes'] == "Issue resolved by resetting password"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_ticket_by_id():
    """Test 4.3: Get ticket by ID."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="ticket3@example.com")
        conversation = await db.create_conversation(customer['id'], "whatsapp")
        ticket = await db.create_ticket(
            customer['id'], conversation['id'], "whatsapp",
            subject="WhatsApp issue"
        )

        retrieved = await db.get_ticket_by_id(ticket['id'])

        assert retrieved is not None
        assert retrieved['subject'] == "WhatsApp issue"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_customer_tickets():
    """Test 4.4: List customer tickets."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="tickets@example.com")
        conversation = await db.create_conversation(customer['id'], "email")

        # Create multiple tickets
        await db.create_ticket(customer['id'], conversation['id'], "email", subject="Ticket 1")
        await db.create_ticket(customer['id'], conversation['id'], "email", subject="Ticket 2")
        await db.create_ticket(customer['id'], conversation['id'], "email", subject="Ticket 3")

        tickets = await db.get_customer_tickets(customer['id'])

        assert len(tickets) == 3
    finally:
        await conn.close()


# ============================================================================
# TEST 5: Knowledge Base
# ============================================================================

@pytest.mark.asyncio
async def test_search_returns_results():
    """Test 5.1: Search returns results."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        # Insert test entry
        await conn.execute(
            """
            INSERT INTO knowledge_base (title, content, category, tags)
            VALUES ($1, $2, $3, $4)
            """,
            "Login Issues",
            "If you cannot login, try resetting your password.",
            "Support",
            ["login", "password", "support"]
        )

        results = await db.search_knowledge_base("login")

        assert len(results) > 0
        assert "Login Issues" in [r['title'] for r in results]
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_category_filter_works():
    """Test 5.2: Category filter works."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        await conn.execute(
            """
            INSERT INTO knowledge_base (title, content, category, tags)
            VALUES ($1, $2, $3, $4)
            """,
            "API Documentation",
            "API usage guide",
            "API",
            ["api", "developer"]
        )
        await conn.execute(
            """
            INSERT INTO knowledge_base (title, content, category, tags)
            VALUES ($1, $2, $3, $4)
            """,
            "Billing FAQ",
            "Billing questions",
            "Billing",
            ["billing", "payment"]
        )

        api_results = await db.search_knowledge_base("guide", category="API")
        billing_results = await db.search_knowledge_base("guide", category="Billing")

        assert len(api_results) == 1
        assert len(billing_results) == 0
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_empty_search_handled():
    """Test 5.3: Empty search handled."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        results = await db.search_knowledge_base("nonexistent_term_xyz")

        assert isinstance(results, list)
    finally:
        await conn.close()


# ============================================================================
# TEST 6: Metrics
# ============================================================================

@pytest.mark.asyncio
async def test_record_metric():
    """Test 6.1: Record metric."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        success = await db.record_metric(
            name="response_time",
            value=150.5,
            channel="email",
            dimensions={"avg": True}
        )

        assert success is True
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_get_metrics_by_channel():
    """Test 6.2: Get metrics by channel."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        await db.record_metric("latency", 100.0, "email")
        await db.record_metric("latency", 200.0, "whatsapp")
        await db.record_metric("latency", 150.0, "email")

        metrics = await db.get_metrics_by_channel(hours=24)

        assert "email" in metrics
        assert "whatsapp" in metrics
        assert len(metrics["email"]) == 2
        assert len(metrics["whatsapp"]) == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_calculate_escalation_rate():
    """Test 6.3: Calculate escalation rate."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        customer = await db.create_customer(email="escalation@example.com")
        conversation = await db.create_conversation(customer['id'], "email")

        # Create tickets with different statuses
        ticket1 = await db.create_ticket(customer['id'], conversation['id'], "email")
        ticket2 = await db.create_ticket(customer['id'], conversation['id'], "email")

        await conn.execute(
            "UPDATE tickets SET status = 'escalated' WHERE id = $1::uuid",
            str(ticket1['id'])
        )
        await conn.execute(
            "UPDATE tickets SET status = 'resolved' WHERE id = $1::uuid",
            str(ticket2['id'])
        )

        rate = await db.get_escalation_rate(hours=24)

        assert rate == 0.5  # 1 out of 2 escalated
    finally:
        await conn.close()


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_customer_journey():
    """Test: Complete customer support journey."""
    params = get_connection_params()
    conn = await asyncpg.connect(**params)
    try:
        await clean_db(conn)
        # 1. Customer contacts support
        customer = await db.get_or_create_customer(
            "journey@example.com",
            "email"
        )

        # 2. Create conversation
        conversation = await db.create_conversation(
            customer['id'],
            "email"
        )

        # 3. Customer sends message
        await db.save_message(
            conversation['id'],
            "email",
            "inbound",
            "customer",
            "I cannot access my account. Please help!",
            sentiment_score=0.3
        )

        # 4. Agent responds
        await db.save_message(
            conversation['id'],
            "email",
            "outbound",
            "agent",
            "I'd be happy to help you regain access.",
            latency_ms=200
        )

        # 5. Create ticket
        ticket = await db.create_ticket(
            customer['id'],
            conversation['id'],
            "email",
            category="Account Access",
            priority="high",
            subject="Cannot access account"
        )

        # 6. Update sentiment
        await db.update_conversation_sentiment(
            conversation['id'],
            0.5,
            'improving'
        )

        # 7. Resolve ticket
        await db.update_ticket_status(
            ticket['id'],
            'resolved',
            "Password reset link sent"
        )

        # 8. Close conversation
        await db.update_conversation_status(
            conversation['id'],
            'resolved',
            ended_at=True
        )

        # Verify
        history = await db.get_customer_history(customer['id'])
        assert len(history) == 1

        tickets = await db.get_customer_tickets(customer['id'])
        assert len(tickets) == 1
        assert tickets[0]['status'] == 'resolved'
    finally:
        await conn.close()
