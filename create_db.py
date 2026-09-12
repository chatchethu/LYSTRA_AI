import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect(user='postgres', password='postgres', host='localhost', database='postgres')
        await conn.execute('CREATE DATABASE personalai;')
        await conn.close()
        print("Database 'personalai' created successfully.")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Database 'personalai' already exists.")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
