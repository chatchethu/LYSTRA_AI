# NOVA AI Architecture Inventory

:# 1. Request Flow
- HTTP requests come into `backend/main.py` via FastAPI.
- Auth middleware (`get_current_user`) verifies JWT and user activity.
- Routes are in `backend/api/`. Most business logic is handled in routes or passed to specific managers.
- Responses are returned as JSON, or as Server-Sent Events via `StreamingResponse` for chat.

## 2. Authentication Flow
- Handled in `backend/api/auth.py` and `backend/auth/service.py`.
- Uses bcrypt for passwords, PyJWT for tokens.
- Supports short-lived access tokens and long-lived refresh tokens.
- Includes a Redis-based token blocklist for proper revocation on logout.

## 3. Chat and Streaming Flow
- Chat requests hit `POST /api/chat` or `POST /api/chat/stream`.
- Both paths instantiate `ConversationEngine` (in `backend/orchestration/conversation_engine.py`).
- The engine uses `ConversationUnderstander` -> `EmotionAnalyzer` -> `ComplexityRouter` -> `AgenticEngine`/hToolRouter` -> `LLM` -> `ResponseNormalizer`.
- Streaming uses an `asyncio.Queue` to yield `chunk`, `blocks_update`, `status`, and `error` events to the frontend.

## 4. Memory Flow
- Managed in `backend/memory/service.py` via `MemoryService`.
- Uses PostgreSQL with `pgvector` for storage.
- Auto-extracts memories using regex heuristics and categorizes them.
- Uses `OllamaProvider.embed()` to generate vector embeddings.
- Retrieves relevant context using `<=>` (cosine distance).

## 5. Task and Tool Flow
- `Task`s are defined in `backend/planning/task_manager.py` (which was unused/broken).
- `ToolRegistry` in `backend/tools/registry.py` registers and invokes tools.
- `ToolDecisionEngine` decides if tools are needed.

## 6. Model Flow
- `LLMGateway` abstracts the provider.
- `OllamaProvider` is the implementation for local models.
- `ModelRouter` selects the specific model based on task type (e.g. Chat vs Routing).

## 7. Duplicate Implementations Found
- **Orchestration**: `ConversationEngine`, `AgenticEngine`, `AgentLoop`, `Supervisor`, `AgentRuntime` are all competing orchestration/agent loops.
- **Memory**: `MemoryManager`, `MemoryService`, `LongTermMemory`, `ContextManager` have overlapping responsibilities.
- **Tools**: Multiple routing mechanisms (e.g., `ToolRouter`, `ToolDecisionEngine`).

## 8. Mock/Unsafe/Incomplete Code
- `pass`: 124 occurrences
- `return None`: 37 occurrences
- `return []`: 18 occurrences
- `mock`: 67 occurrences
- `placeholder`: 21 occurrences
- `uuid.uuid4()` : 16 occurrences (often used for fake IDs or default tokens)
- `current_user` / `get_current_user` : 77 / 45 occurrences (lots of dependency overrides or mocks in scripts)
- `create_all`: 1 occurrence (in `backend/db/session.py`)

## 9. Hardcoded Configuration
- Found `localhost` referenced 34 times, primarily in config and docker-compose files.

## 10. Baseline Test Results
- Ran `pytest`.
- 36 failed, 32 passed, 5 errors.
- **Errors include**:
  - `AttributeError: 'ConversationState' object has no attribute 'session_context'`
  - `AttributeError: 'ToolRegistry' object has no attribute 'get'`
  - DB connection errors (e.g. asyncpg connection refused in some tests).
- Fixed `ImportError` for `ResponseDecision` to allow the test suite to execute and produce this baseline.