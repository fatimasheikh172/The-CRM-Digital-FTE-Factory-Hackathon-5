import asyncio
import asyncpg
from database import queries as db

async def test():
    # Test direct connection
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        database='fte_db',
        user='fte_user',
        password='fte_password123'
    )
    print('✓ Connected to PostgreSQL')
    
    # Test create customer
    customer = await db.create_customer('test@test.com', '+123', 'Test')
    print(f'✓ Created customer: {customer}')
    
    # Clean up
    await conn.execute("DELETE FROM customers WHERE email = 'test@test.com'")
    await conn.close()
    print('✓ Test complete!')

if __name__ == '__main__':
    asyncio.run(test())
