import asyncio
import asyncpg

async def test():
    print("Trying to connect...")
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        database='fte_db',
        user='fte_user',
        password='fte_password123'
    )
    result = await conn.fetchval('SELECT version()')
    print(f"Connected! PostgreSQL: {result}")
    await conn.close()

asyncio.run(test())
