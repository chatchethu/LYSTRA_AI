# NOVA WEB SEARCH AUDIT

## Current Search Path
- ackend/tools/web/web_search.py contains WebSearchTool which currently uses duckduckgo_search (DDGS).
- Environment contains FIRECRAWL_API_KEY indicating a move towards Firecrawl.

## Current Source Path & Citation Path
- In ackend/agent/runtime.py, sources are extracted if the tool result is a dict with 'sources'. The tool results are appended directly to the LLM context.

## Tool Architecture Integration
- Tools are managed via ackend/tools/registry.py.
- Execution is handled via ackend/tools/tool_router.py or directly via AgentRuntime's single_tool execution mode.
- The AgentRuntime uses ToolExecutor (for multi-step) and ToolRegistry (egistry.get_tool()).

## Gaps Identified
- Missing a robust WebSearchDecision engine. Right now, _decide_execution_mode hardcodes research intent to 'single_tool' with ['web_search'].
- Missing SearchQueryBuilder and contextual resolution.
- Search result normalization is not standardized to a SearchResult schema.
- Citations are currently injected into the UI via the frontend interpreting tool blocks, but source mapping to factual claims is not deeply enforced.
