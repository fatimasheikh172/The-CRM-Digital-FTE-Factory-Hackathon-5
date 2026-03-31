"""
Test connection with fte_user credentials
"""

import asyncio
import asyncpg


async def test_connection():
    """Test connection with fte_user."""
    print("Testing connection with fte_user credentials...")
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            database='fte_db',
            user='fte_user',
            password='fte_password123'
        )
        
        print("✓ Connected successfully as fte_user!")
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"\nExisting tables: {[row['table_name'] for row in tables]}")
        
        await conn.close()
        return True
        
    except asyncpg.InvalidPasswordError as e:
        print(f"✗ Invalid password: {e}")
        return False
    except asyncpg.PostgresError as e:
        print(f"✗ PostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_connection())
    exit(0 if result else 1)
