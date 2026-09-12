with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix 1: Cache TTL for partial failures & try/except
old_cache = '''        await self.redis.setex(cache_key, self._cache_ttl, json.dumps(final_data))'''

new_cache = '''        try:
            ttl = 60 if failed_queries else self._cache_ttl
            await self.redis.setex(cache_key, ttl, json.dumps(final_data))
        except Exception as e:
            logger.warning("web_search_cache_set_failed", error=str(e))'''

content = content.replace(old_cache, new_cache)

# Fix 2: Unused TaskType
old_import = '''            from backend.llm.model_router import TaskType
            model = getattr(model_router, "default_model", "llama3.2:latest")'''

new_import = '''            model = getattr(model_router, "default_model", "llama3.2:latest")'''

content = content.replace(old_import, new_import)

# Fix 3: Clamp confidence
old_conf = '''                            retrieved_at=r["retrieved_at"],
                            confidence=r["relevance_score"] / 2.0
                        )'''

new_conf = '''                            retrieved_at=r["retrieved_at"],
                            confidence=min(1.0, max(0.0, r["relevance_score"] / 2.0))
                        )'''

content = content.replace(old_conf, new_conf)

# Fix 4: Budget deduction
old_budget = '''        if budget:
            cost = len(search_queries) * 0.1
            budget.deduct_cost(cost)
            logger.info("web_search_cost_deducted", cost=cost, queries_count=len(search_queries))'''

new_budget = '''        if budget:
            cost = len(search_queries) * 0.1
            try:
                if hasattr(budget, 'remaining') and budget.remaining < cost:
                    return ToolResult(success=False, data=None, error="Insufficient budget for web search.")
                budget.deduct_cost(cost)
                logger.info("web_search_cost_deducted", cost=cost, queries_count=len(search_queries))
            except Exception as e:
                logger.warning("budget_deduction_failed", error=str(e))'''

content = content.replace(old_budget, new_budget)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("web_search.py partial patch 2 applied")
