"""
Run database tests directly without pytest.
"""

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


def get_connection_params():
    """Get database connection parameters."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5433)),
        'database': os.getenv('DB_NAME', 'fte_db'),
        'user': os.getenv('DB_USER', 'fte_user'),
        'password': os.getenv('DB_PASSWORD', 'fte_password123')
    }


async def get_conn():
    """Get a database connection."""
    params = get_connection_params()
    return await asyncpg.connect(**params)


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


async def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("TechCorp Customer Success Agent - Database Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # Test 1: Connect to PostgreSQL
    print("\n[1/25] test_connect_to_postgresql...", end=" ")
    try:
        params = get_connection_params()
        conn = await asyncpg.connect(**params)
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        assert result == 1
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 2: All tables exist
    print("[2/25] test_all_tables_exist...", end=" ")
    try:
        conn = await get_conn()
        expected_tables = [
            'customers', 'customer_identifiers', 'conversations', 'messages',
            'tickets', 'knowledge_base', 'agent_metrics', 'escalations'
        ]
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name
        """)
        table_names = [row['table_name'] for row in tables]
        await conn.close()
        for table in expected_tables:
            assert table in table_names, f"Table '{table}' not found"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 3: All indexes exist
    print("[3/25] test_all_indexes_exist...", end=" ")
    try:
        conn = await get_conn()
        expected_indexes = [
            'idx_customers_email', 'idx_customers_phone',
            'idx_customer_identifiers_value', 'idx_conversations_customer',
            'idx_conversations_status', 'idx_conversations_channel',
            'idx_messages_conversation', 'idx_messages_channel',
            'idx_tickets_status', 'idx_tickets_channel',
            'idx_tickets_customer', 'idx_escalations_ticket',
            'idx_agent_metrics_recorded'
        ]
        indexes = await conn.fetch("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """)
        index_names = [row['indexname'] for row in indexes]
        await conn.close()
        for index in expected_indexes:
            assert index in index_names, f"Index '{index}' not found"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 4: Create customer
    print("[4/25] test_create_customer...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(
            email="test@example.com",
            phone="+1234567890",
            name="Test Customer"
        )
        await conn.close()
        assert customer is not None
        assert customer['email'] == "test@example.com"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 5: Find customer by email
    print("[5/25] test_find_customer_by_email...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        await db.create_customer(email="findme@example.com", name="Find Me")
        customer = await db.find_customer_by_email("findme@example.com")
        await conn.close()
        assert customer is not None
        assert customer['email'] == "findme@example.com"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 6: Find customer by phone
    print("[6/25] test_find_customer_by_phone...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        await db.create_customer(phone="+9876543210", name="Phone Customer")
        customer = await db.find_customer_by_phone("+9876543210")
        await conn.close()
        assert customer is not None
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 7: Get or create customer
    print("[7/25] test_get_or_create_customer...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer1 = await db.get_or_create_customer("newcustomer@example.com", "email")
        customer2 = await db.get_or_create_customer("newcustomer@example.com", "email")
        await conn.close()
        assert customer1 is not None
        assert customer2 is not None
        assert customer2['id'] == customer1['id']
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 8: Update customer
    print("[8/25] test_update_customer...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="update@example.com", name="Original Name")
        await conn.execute(
            "UPDATE customers SET name = $1, updated_at = NOW() WHERE id = $2",
            "Updated Name", customer['id']
        )
        updated = await db.find_customer_by_email("update@example.com")
        await conn.close()
        assert updated['name'] == "Updated Name"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 9: Create conversation
    print("[9/25] test_create_conversation...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="conv@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="email")
        await conn.close()
        assert conversation is not None
        assert conversation['initial_channel'] == "email"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 10: Add messages
    print("[10/25] test_add_messages...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="messages@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="whatsapp")
        msg1 = await db.save_message(
            conversation_id=conversation['id'], channel="whatsapp",
            direction="inbound", role="customer",
            content="Hello, I need help", sentiment_score=0.5
        )
        msg2 = await db.save_message(
            conversation_id=conversation['id'], channel="whatsapp",
            direction="outbound", role="agent",
            content="How can I help?", latency_ms=150
        )
        await conn.close()
        assert msg1 is not None
        assert msg2 is not None
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 11: Update conversation status
    print("[11/25] test_update_conversation_status...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="status@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="email")
        success = await db.update_conversation_status(conversation['id'], 'resolved', ended_at=True)
        await conn.close()
        assert success is True
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 12: Update conversation sentiment
    print("[12/25] test_update_conversation_sentiment...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="sentiment@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="web_form")
        success = await db.update_conversation_sentiment(conversation['id'], score=0.3, trend='declining')
        await conn.close()
        assert success is True
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 13: Get customer history
    print("[13/25] test_get_customer_history...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="history@example.com")
        await db.create_conversation(customer['id'], "email")
        await db.create_conversation(customer['id'], "whatsapp")
        history = await db.get_customer_history(customer['id'])
        await conn.close()
        assert len(history) == 2
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 14: Create ticket
    print("[14/25] test_create_ticket...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="ticket@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="email")
        ticket = await db.create_ticket(
            customer_id=customer['id'], conversation_id=conversation['id'],
            channel="email", category="Technical", priority="high",
            subject="Cannot login to account"
        )
        await conn.close()
        assert ticket is not None
        assert ticket['priority'] == "high"
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 15: Update ticket status
    print("[15/25] test_update_ticket_status...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="ticket2@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="email")
        ticket = await db.create_ticket(customer['id'], conversation['id'], "email", subject="Test ticket")
        success = await db.update_ticket_status(ticket['id'], 'resolved', notes="Issue resolved")
        await conn.close()
        assert success is True
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 16: Get ticket by ID
    print("[16/25] test_get_ticket_by_id...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="ticket3@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="whatsapp")
        ticket = await db.create_ticket(customer['id'], conversation['id'], "whatsapp", subject="WhatsApp issue")
        retrieved = await db.get_ticket_by_id(ticket['id'])
        await conn.close()
        assert retrieved is not None
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 17: Get customer tickets
    print("[17/25] test_get_customer_tickets...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="tickets@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="email")
        await db.create_ticket(customer['id'], conversation['id'], "email", subject="Ticket 1")
        await db.create_ticket(customer['id'], conversation['id'], "email", subject="Ticket 2")
        await db.create_ticket(customer['id'], conversation['id'], "email", subject="Ticket 3")
        tickets = await db.get_customer_tickets(customer['id'])
        await conn.close()
        assert len(tickets) == 3
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 18: Search knowledge base
    print("[18/25] test_search_returns_results...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        await conn.execute(
            "INSERT INTO knowledge_base (title, content, category, tags) VALUES ($1, $2, $3, $4)",
            "Login Issues", "If you cannot login, try resetting your password.",
            "Support", ["login", "password", "support"]
        )
        results = await db.search_knowledge_base("login")
        await conn.close()
        assert len(results) > 0
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 19: Category filter
    print("[19/25] test_category_filter_works...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        await conn.execute(
            "INSERT INTO knowledge_base (title, content, category, tags) VALUES ($1, $2, $3, $4)",
            "API Documentation", "API usage guide", "API", ["api", "developer"]
        )
        await conn.execute(
            "INSERT INTO knowledge_base (title, content, category, tags) VALUES ($1, $2, $3, $4)",
            "Billing FAQ", "Billing questions", "Billing", ["billing", "payment"]
        )
        api_results = await db.search_knowledge_base("guide", category="API")
        billing_results = await db.search_knowledge_base("guide", category="Billing")
        await conn.close()
        assert len(api_results) == 1
        assert len(billing_results) == 0
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 20: Empty search
    print("[20/25] test_empty_search_handled...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        results = await db.search_knowledge_base("nonexistent_term_xyz")
        await conn.close()
        assert isinstance(results, list)
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 21: Record metric
    print("[21/25] test_record_metric...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        success = await db.record_metric(
            name="response_time", value=150.5,
            channel="email", dimensions={"avg": True}
        )
        await conn.close()
        assert success is True
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 22: Get metrics by channel
    print("[22/25] test_get_metrics_by_channel...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        await db.record_metric("latency", 100.0, "email")
        await db.record_metric("latency", 200.0, "whatsapp")
        await db.record_metric("latency", 150.0, "email")
        metrics = await db.get_metrics_by_channel(hours=24)
        await conn.close()
        assert "email" in metrics
        assert "whatsapp" in metrics
        assert len(metrics["email"]) == 2
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 23: Calculate escalation rate
    print("[23/25] test_calculate_escalation_rate...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.create_customer(email="escalation@example.com")
        conversation = await db.create_conversation(customer_id=customer['id'], channel="email")
        ticket1 = await db.create_ticket(customer['id'], conversation['id'], "email")
        ticket2 = await db.create_ticket(customer['id'], conversation['id'], "email")
        await conn.execute("UPDATE tickets SET status = $1 WHERE id = $2", "escalated", ticket1['id'])
        await conn.execute("UPDATE tickets SET status = $1 WHERE id = $2", "resolved", ticket2['id'])
        rate = await db.get_escalation_rate(hours=24)
        await conn.close()
        assert rate == 0.5
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 24: Full customer journey
    print("[24/25] test_full_customer_journey...", end=" ")
    try:
        conn = await get_conn()
        await clean_db(conn)
        customer = await db.get_or_create_customer("journey@example.com", "email")
        conversation = await db.create_conversation(customer['id'], "email")
        await db.save_message(conversation['id'], "email", "inbound", "customer",
                             "I cannot access my account!", sentiment_score=0.3)
        await db.save_message(conversation['id'], "email", "outbound", "agent",
                             "I'd be happy to help.", latency_ms=200)
        ticket = await db.create_ticket(customer['id'], conversation['id'], "email",
                                       category="Account Access", priority="high",
                                       subject="Cannot access account")
        await db.update_conversation_sentiment(conversation['id'], 0.5, 'improving')
        await db.update_ticket_status(ticket['id'], 'resolved', "Password reset link sent")
        await db.update_conversation_status(conversation['id'], 'resolved', ended_at=True)
        history = await db.get_customer_history(customer['id'])
        tickets = await db.get_customer_tickets(customer['id'])
        await conn.close()
        assert len(history) == 1
        assert len(tickets) == 1
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Test 25: Search knowledge base returns content
    print("[25/25] test_kb_content...", end=" ")
    try:
        conn = await get_conn()
        results = await db.search_knowledge_base("login")
        await conn.close()
        assert isinstance(results, list)
        print("✓ PASSED")
        passed += 1
    except Exception as e:
        print(f"✗ FAILED: {e}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
