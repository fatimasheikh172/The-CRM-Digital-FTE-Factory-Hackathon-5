"""
Apply Database Schema Script

Applies the complete schema to the running PostgreSQL database.

If you see "role does not exist" error, run setup first:
  - Windows: database\setup.bat
  - Python: python database\docker_setup.py
  - Docker: docker exec fte_postgres psql -U postgres -c "CREATE USER fte_user WITH PASSWORD 'fte_password123';"
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def apply_schema():
    """Apply the schema to the database."""
    print("=" * 60)
    print("TechCorp Customer Success Agent - Schema Application")
    print("=" * 60)
    
    # Database configuration
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 5432))
    database = os.getenv('DB_NAME', 'fte_db')
    user = os.getenv('DB_USER', 'fte_user')
    password = os.getenv('DB_PASSWORD', 'fte_password123')
    
    print(f"\nConnecting to PostgreSQL at {host}:{port}/{database}...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        print("Connected successfully!")
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        print(f"\nApplying schema from database/schema.sql...")
        
        # Execute schema
        await conn.execute(schema)
        
        print("Schema applied successfully!")
        
        # Verify tables were created
        print("\nVerifying tables...")
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """
        tables = await conn.fetch(tables_query)
        table_names = [row['table_name'] for row in tables]
        
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
        
        print("\nTables created:")
        for table in expected_tables:
            status = "✓" if table in table_names else "✗"
            print(f"  {status} {table}")
        
        # Verify indexes
        print("\nVerifying indexes...")
        indexes_query = """
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE 'idx_%'
            ORDER BY indexname
        """
        indexes = await conn.fetch(indexes_query)
        index_names = [row['indexname'] for row in indexes]
        
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
        
        print("\nIndexes created:")
        for index in expected_indexes:
            status = "✓" if index in index_names else "✗"
            print(f"  {status} {index}")
        
        # Close connection
        await conn.close()
        
        print("\n" + "=" * 60)
        print(f"Schema application complete!")
        print(f"Tables: {len(expected_tables)}")
        print(f"Indexes: {len(expected_indexes)}")
        print("=" * 60)
        
        return True

    except asyncpg.InvalidPasswordError as e:
        print(f"\n❌ PostgreSQL authentication error: {e}")
        print("\n" + "=" * 60)
        print("SETUP REQUIRED")
        print("=" * 60)
        print("\nThe database user 'fte_user' does not exist or has wrong password.")
        print("\nRun setup first (choose one):")
        print("  1. Windows batch:  database\\setup.bat")
        print("  2. Python script:  python database\\docker_setup.py")
        print("  3. Manual Docker:  docker exec fte_postgres psql -U postgres -c \"CREATE USER fte_user WITH PASSWORD 'fte_password123';\"")
        print("=" * 60)
        return False
    except asyncpg.PostgresError as e:
        error_msg = str(e)
        print(f"\n❌ PostgreSQL error: {e}")
        
        # Check for specific errors
        if "role" in error_msg.lower() and "does not exist" in error_msg.lower():
            print("\n" + "=" * 60)
            print("SETUP REQUIRED - User does not exist")
            print("=" * 60)
            print("\nRun setup first (choose one):")
            print("  1. Windows batch:  database\\setup.bat")
            print("  2. Python script:  python database\\docker_setup.py")
            print("  3. Manual Docker:")
            print('     docker exec fte_postgres psql -U postgres -c "CREATE USER fte_user WITH PASSWORD \'fte_password123\';"')
            print("=" * 60)
        return False
    except FileNotFoundError as e:
        print(f"\n❌ Schema file not found: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(apply_schema())
    exit(0 if success else 1)
