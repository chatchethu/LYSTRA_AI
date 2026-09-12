import asyncio
from backend.tools.web.web_search import WebSearchTool

async def test_search():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    tool = WebSearchTool()
    import uuid
    dummy_uid = uuid.uuid4()
    # Execute web search
    result = await tool.execute(user_id=dummy_uid, query="Latest AI news today", freshness_required=True)
    print("Success:", result.success)
    print("Result data:", result.data)

asyncio.run(test_search())
