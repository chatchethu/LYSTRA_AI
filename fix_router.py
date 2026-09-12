with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_timeout = '''        except asyncio.TimeoutError:
            logger.warning("tool_router_llm_timeout")
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.MANDATORY_WEB,
                reasoning="LLM routing timed out; defaulting to optional web.",
                route_priority=RoutePriority.TASK, 
                confidence=0.3
            )
        except Exception as e:
            logger.warning("tool_router_llm_failed", error=str(e))
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.MANDATORY_WEB,
                reasoning="Fallback due to error", 
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )'''

new_timeout = '''        except asyncio.TimeoutError:
            logger.warning("tool_router_llm_timeout")
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="LLM routing timed out; safely defaulting to NO_WEB conversation.",
                route_priority=RoutePriority.CONVERSATION, 
                confidence=0.3
            )
        except Exception as e:
            logger.warning("tool_router_llm_failed", error=str(e))
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Fallback due to error; safely defaulting to NO_WEB conversation.", 
                route_priority=RoutePriority.CONVERSATION,
                confidence=0.3
            )'''

content = content.replace(old_timeout, new_timeout)
content = content.replace('timeout=15.0', 'timeout=120.0')

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ToolRouter catastrophic web search fallback")
