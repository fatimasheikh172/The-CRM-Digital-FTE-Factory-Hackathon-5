"""
Test Database Connection
"""

import asyncio
import asyncpg


async def test_connection():
    """Test connection with various credentials."""
    print("Testing PostgreSQL connections...")
    
    # Try the credentials from the task description
    configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'fte_db',
            'user': 'fte_user',
            'password': 'fte_password123'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': ''
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\nTrying config {i}: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
        try:
            conn = await asyncpg.connect(**config)
            print(f"✓ Success with config {i}!")
            
            # Check databases
            databases = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false")
            print(f"Databases: {[row['datname'] for row in databases]}")
            
            # Check if fte_db exists
            if 'fte_db' in [row['datname'] for row in databases]:
                print("fte_db exists!")
                await conn.close()
                return config
            else:
                print("fte_db does not exist. Need to create it.")
                await conn.close()
                return config
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    return None


if __name__ == "__main__":
    config = asyncio.run(test_connection())
    if config:
        print(f"\nUsing config: {config}")
    else:
        print("\nNo working config found!")
