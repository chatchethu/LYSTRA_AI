# Service Level Objectives (SLOs) & Alerts - Phase 76

This document defines the formal Service Level Objectives for the NOVA AI agent platform and specifies how they should be monitored using Prometheus and Grafana.

## 1. Availability

**API Availability**
- **SLI**: Percentage of HTTP requests to `/api/*` (excluding `/api/v1/agent/*`) that return HTTP 2xx, 3xx, or 4xx (client errors). 5xx errors count against the budget.
- **SLO**: 99.9% uptime over a 30-day window.

**Chat & SSE Availability**
- **SLI**: Percentage of `/api/v1/messages/*` requests that successfully establish an SSE stream and emit a `[DONE]` terminator.
- **SLO**: 99.5% uptime.

## 2. Latency

**First Token Latency (Time to First Byte - TTFB)**
- **SLI**: The elapsed time between a user sending a chat message and the server emitting the first `message.delta` SSE event.
- **SLO**: < 1.5 seconds at the 90th percentile (P90), < 3 seconds at P99.

**Task Completion Latency**
- **SLI**: Time taken for a background Celery task (e.g., document parsing) to transition from `pending` to `ready`.
- **SLO**: < 5 minutes for files under 5MB at the 95th percentile (P95).

**Memory Retrieval Latency**
- **SLI**: pgvector cosine similarity search duration.
- **SLO**: < 250 milliseconds at P95.

## 3. Reliability & Correctness

**Tool Success Rate**
- **SLI**: Percentage of tool invocations (via ToolExecutor) that yield a successful `ActionResult` vs throwing an unhandled exception or timeout.
- **SLO**: > 95% over a 7-day window.

**Task Success Rate**
- **SLI**: Percentage of background agent tasks that complete successfully without exhausting retries.
- **SLO**: > 99%.

## Recommended Alerts

- **Critical Alert**: `API_Error_Rate_High` (if 5xx rate > 1% for 5 minutes).
- **Critical Alert**: `LLM_Timeout_Spike` (if Ollama/Gateway timeout rate > 5% for 10 minutes).
- **Warning Alert**: `Queue_Depth_High` (if Celery `agent_tasks` queue > 100 items for 15 minutes).
- **Warning Alert**: `First_Token_Latency_Degraded` (if P90 TTFB > 2.5s for 30 minutes).

