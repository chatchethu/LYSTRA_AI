with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix C & D: WebSearch cascading on rate limits
old_firecrawl = '''                    elif resp.status_code == 429:
                        logger.warning("firecrawl_rate_limited", status=resp.status_code)
                        await self.firecrawl_circuit_breaker.record_failure()
                    else:'''

new_firecrawl = '''                    elif resp.status_code == 429:
                        logger.warning("firecrawl_rate_limited", status=resp.status_code)
                        await self.firecrawl_circuit_breaker.record_failure()
                        # Cascade to Tavily/DDG immediately instead of retrying the same rate-limited provider.
                        current_firecrawl_key = None
                    else:'''

content = content.replace(old_firecrawl, new_firecrawl)

old_tavily = '''                    elif resp.status_code == 429:
                        logger.warning("tavily_rate_limited", status=resp.status_code)
                        await self.tavily_circuit_breaker.record_failure()
                        await asyncio.sleep(2.0)
                    else:'''

new_tavily = '''                    elif resp.status_code == 429:
                        logger.warning("tavily_rate_limited", status=resp.status_code)
                        await self.tavily_circuit_breaker.record_failure()
                        # Cascade to DDG immediately instead of retrying the same rate-limited provider.
                        current_tavily_key = None
                    else:'''

content = content.replace(old_tavily, new_tavily)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched WebSearch tool")
