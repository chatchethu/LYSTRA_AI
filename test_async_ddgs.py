import asyncio
from ddgs import AsyncDDGS

async def run():
    try:
        async with AsyncDDGS() as ddgs:
            # Note: in older ddgs it might be an async generator
            results = []
            async for r in ddgs.text('latest ai news today', max_results=2):
                results.append(r)
            print(results)
    except Exception as e:
        print("Error:", e)

asyncio.run(run())
