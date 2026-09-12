with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# 1. Add timeout to DDGS
old_ddgs = '''                    if not current_firecrawl_key and not current_tavily_key:
                        duckduckgo_fallback_count += 1
                        from ddgs import DDGS
                        with DDGS() as ddgs:
                            def search_func(query, n):'''

new_ddgs = '''                    if not current_firecrawl_key and not current_tavily_key:
                        duckduckgo_fallback_count += 1
                        from ddgs import DDGS
                        with DDGS(timeout=10) as ddgs:
                            def search_func(query, n):'''

content = content.replace(old_ddgs, new_ddgs)

# 2. Fix gather and CancelledError handling
old_gather = '''        tasks = [do_search(q, firecrawl_key, tavily_key) for q in search_queries]
        try:
            results_gathered = await asyncio.wait_for(asyncio.gather(*tasks), timeout=self.settings.WEB_SEARCH_OUTER_TIMEOUT)
            for i, (success, local_results) in enumerate(results_gathered):
                if success:
                    raw_results.extend([r.model_dump() for r in local_results])
                else:
                    failed_queries.append(search_queries[i])
        except asyncio.TimeoutError:
            logger.warning("web_search_timeout_exceeded")
            failed_queries.extend(search_queries)'''

new_gather = '''        tasks = [asyncio.create_task(do_search(q, firecrawl_key, tavily_key)) for q in search_queries]
        try:
            results_gathered = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=self.settings.WEB_SEARCH_OUTER_TIMEOUT)
            for i, result in enumerate(results_gathered):
                if isinstance(result, Exception):
                    logger.warning("web_search_task_failed", error=str(result), query=search_queries[i])
                    failed_queries.append(search_queries[i])
                elif isinstance(result, tuple) and result[0]:
                    raw_results.extend([r.model_dump() for r in result[1]])
                else:
                    failed_queries.append(search_queries[i])
        except asyncio.TimeoutError:
            logger.warning("web_search_timeout_exceeded")
            failed_queries.extend(search_queries)
        finally:
            # Ensure we don't leave tasks dangling if we are cancelled
            for t in tasks:
                if not t.done():
                    t.cancel()'''

content = content.replace(old_gather, new_gather)

# 3. Catch BaseException to log if do_search was cancelled abruptly? Actually CancelledError is fine to propagate if tasks are managed. But I will catch CancelledError and log it in do_search to be safe.
old_except = '''                    if attempt == 1:
                        logger.error("web_search_failed_for_query", error=str(e), query=q)
                        return False, []
                    else:
                        await asyncio.sleep(1.0)
            return False, []'''

new_except = '''                    if attempt == 1:
                        logger.error("web_search_failed_for_query", error=str(e), query=q)
                        return False, []
                    else:
                        await asyncio.sleep(1.0)
                except asyncio.CancelledError:
                    logger.warning("web_search_cancelled_for_query", query=q)
                    raise
            return False, []'''

content = content.replace(old_except, new_except)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("web_search patched with robust gather and timeout")
