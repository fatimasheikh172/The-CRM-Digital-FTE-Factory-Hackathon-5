import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        database='fte_db',
        user='fte_user',
        password='fte_password123'
    )
    result = await conn.fetchval('SELECT 1')
    await conn.close()
    print(f'Connected! Result: {result}')

asyncio.run(test())
