with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_get = '''        if not freshness_required:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.info("web_search_metrics", cache_hit=True, queries=search_queries)
                return ToolResult(success=True, data=json.loads(cached_data))'''

new_get = '''        if not freshness_required:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    logger.info("web_search_metrics", cache_hit=True, queries=search_queries)
                    return ToolResult(success=True, data=json.loads(cached_data))
            except Exception as e:
                logger.warning("web_search_cache_get_failed", error=str(e))'''

content = content.replace(old_get, new_get)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("web_search.py cache get patch applied")
