with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Add to __init__
old_init = '''        self.tavily_circuit_breaker = RedisCircuitBreaker(self.redis, "tavily")'''
new_init = '''        self.tavily_circuit_breaker = RedisCircuitBreaker(self.redis, "tavily")
        self.http_client = httpx.AsyncClient(timeout=10.0)'''
content = content.replace(old_init, new_init)

# Use in Firecrawl search
old_fc = '''                        async with httpx.AsyncClient(timeout=10.0) as client:
                            resp = await client.post('''
new_fc = '''                        if True:
                            resp = await self.http_client.post('''
content = content.replace(old_fc, new_fc)

# Use in Firecrawl scrape
old_sc = '''                        async with httpx.AsyncClient(timeout=10.0) as client:
                            resp = await client.post('''
new_sc = '''                        if True:
                            resp = await self.http_client.post('''
content = content.replace(old_sc, new_sc)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("web_search.py http client patch applied")
