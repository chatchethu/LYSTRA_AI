import re

with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We will regex replace the entire heuristic list section and the deterministic route function
# Basically strip out everything between USER_IDENTITY_TERMS = [ and class ToolRouter:
import ast

def remove_heuristics(source_code):
    lines = source_code.split('\n')
    
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("USER_IDENTITY_TERMS = ["):
            start_idx = i
        if line.startswith("class ToolRouter:"):
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        new_lines = lines[:start_idx] + ["import re", ""] + lines[end_idx:]
        return '\n'.join(new_lines)
    return source_code

content = remove_heuristics(content)

# Now rewrite ToolRouter._deterministic_route to ONLY use the SemanticAnalyzer understanding
old_route = '''    def _deterministic_route(self, message: str, understanding: Any = None) -> Optional[ToolRoutingDecision]:
        if not message:
            return ToolRoutingDecision(web_policy=WebSearchPolicy.NO_WEB, reasoning="Empty message.", route_priority=RoutePriority.CONVERSATION, confidence=1.0)
            
        text = message.lower().strip()
        
        # 1. Identity check first
        if _contains_term(text, USER_IDENTITY_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="User identity question — answered internally.",
                route_priority=RoutePriority.PERSONAL,
                confidence=1.0
            )
            logger.info("tool_router_decision", intent="user_identity", route="PERSONAL", web_policy="NO_WEB", confidence=1.0)
            return result
            
        if _contains_term(text, IDENTITY_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Identity question — answered internally.",
                route_priority=RoutePriority.IDENTITY,
                confidence=1.0
            )
            logger.info("tool_router_decision", intent="identity", route="IDENTITY", web_policy="NO_WEB", confidence=1.0)
            return result
            
        # 2. Deep Research check
        if _contains_term(text, DEEP_RESEARCH_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.DEEP_RESEARCH,
                reasoning="Deep research explicitly requested.",
                route_priority=RoutePriority.TOOL,
                confidence=1.0,
                search_query=_build_search_query(message)
            )
            logger.info("tool_router_decision", intent="deep_research", route="TOOL", web_policy="DEEP_RESEARCH", confidence=1.0)
            return result
            
        # 3. Stable conceptual explanations check
        if any(text.startswith(prefix) for prefix in STATIC_EXPLANATION_PREFIXES):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Stable conceptual explanation does not require web search.",
                route_priority=RoutePriority.TASK,
                confidence=0.95,
            )
            logger.info("tool_router_decision", intent="stable_explanation", route="TASK", web_policy="NO_WEB", confidence=0.95)
            return result

        # 4. Mandatory web check
        if _contains_term(text, MANDATORY_WEB_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.MANDATORY_WEB,
                reasoning="External/current information required.",
                route_priority=RoutePriority.TOOL,
                confidence=0.95,
                search_query=_build_search_query(message)
            )
            logger.info("tool_router_decision", intent="mandatory_web", route="TOOL", web_policy="MANDATORY_WEB", confidence=0.95)
            return result

        # 5. Understanding context check
        if understanding is not None:
            if getattr(understanding, 'is_fallback', False):
                logger.info("tool_router_ignoring_understanding", reason="semantic_analysis_fallback")
                # Do NOT force NO_WEB. Let the LLM decide.
            else:
                raw_intent = getattr(understanding, 'intent', '') or ''
                intent = getattr(raw_intent, 'primary', str(raw_intent))
                speech_act = getattr(understanding, 'speech_act', '') or ''
                
                CASUAL_INTENTS = {"greeting", "casual_conversation", "small_talk", "farewell", "social", "conversation"}
                PERSONAL_INTENTS = {"emotional_support", "venting", "complaint", "personal_sharing"}
                
                if intent in CASUAL_INTENTS or speech_act in ("greeting", "farewell", "small_talk"):
                    result = ToolRoutingDecision(
                        web_policy=WebSearchPolicy.NO_WEB,
                        reasoning=f"Casual conversation intent={intent}.",
                        route_priority=RoutePriority.CONVERSATION,
                        confidence=1.0
                    )
                    logger.info("tool_router_decision", intent=intent, route="CONVERSATION", web_policy="NO_WEB", confidence=1.0)
                    return result
                    
                if intent in PERSONAL_INTENTS:
                    result = ToolRoutingDecision(
                        web_policy=WebSearchPolicy.NO_WEB,
                        reasoning=f"Personal/emotional conversation intent={intent}.",
                        route_priority=RoutePriority.PERSONAL,
                        confidence=1.0
                    )
                    logger.info("tool_router_decision", intent=intent, route="PERSONAL", web_policy="NO_WEB", confidence=1.0)
                    return result
                
        # 6. Heuristic casual check
        if _contains_term(text, CASUAL_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Casual greeting matched.",
                route_priority=RoutePriority.CONVERSATION,
                confidence=0.9
            )
            logger.info("tool_router_decision", intent="casual_match", route="CONVERSATION", web_policy="NO_WEB", confidence=0.9)
            return result

        if _contains_term(text, PERSONAL_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Personal/emotional content matched.",
                route_priority=RoutePriority.PERSONAL,
                confidence=0.9
            )
            logger.info("tool_router_decision", intent="personal_match", route="PERSONAL", web_policy="NO_WEB", confidence=0.9)
            return result

        return None'''

new_route = '''    def _deterministic_route(self, message: str, understanding: Any = None) -> Optional[ToolRoutingDecision]:
        if not message:
            return ToolRoutingDecision(web_policy=WebSearchPolicy.NO_WEB, reasoning="Empty message.", route_priority=RoutePriority.CONVERSATION, confidence=1.0)

        # We rely strictly on SemanticUnderstanding (which is generated by the LLM).
        # ZERO hardcoded string heuristics are used, preventing brittle matches.
        if understanding is not None and not getattr(understanding, 'is_fallback', False):
            raw_intent = getattr(understanding, 'intent', '') or ''
            intent = getattr(raw_intent, 'primary', str(raw_intent))
            
            CASUAL_INTENTS = {"greeting", "casual_conversation", "small_talk", "farewell", "social", "conversation"}
            PERSONAL_INTENTS = {"emotional_support", "venting", "complaint", "personal_sharing"}
            
            if intent in CASUAL_INTENTS:
                result = ToolRoutingDecision(
                    web_policy=WebSearchPolicy.NO_WEB,
                    reasoning=f"Casual conversation intent={intent}.",
                    route_priority=RoutePriority.CONVERSATION,
                    confidence=1.0
                )
                logger.info("tool_router_decision", intent=intent, route="CONVERSATION", web_policy="NO_WEB", confidence=1.0)
                return result
                
            if intent in PERSONAL_INTENTS:
                result = ToolRoutingDecision(
                    web_policy=WebSearchPolicy.NO_WEB,
                    reasoning=f"Personal/emotional conversation intent={intent}.",
                    route_priority=RoutePriority.PERSONAL,
                    confidence=1.0
                )
                logger.info("tool_router_decision", intent=intent, route="PERSONAL", web_policy="NO_WEB", confidence=1.0)
                return result

        return None'''

content = content.replace(old_route, new_route)

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed hardcoded heuristic routing lists entirely.")
