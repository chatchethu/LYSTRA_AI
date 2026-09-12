import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect(user='personalai', password='personalai', host='localhost', port=5433, database='personalai')
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
        await conn.close()
        print("Extension 'vector' created successfully.")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
