# The Autonomous NOVA Architecture (Phase 112)

This document represents the finalized macro-architecture of the NOVA intelligence platform.

```mermaid
flowchart TD
    Client[User / API Request] --> Identity[Identity Layer JWT/RBAC]
    Identity --> Firewall[Policy / Agent Firewall]
    Firewall --> Supervisor[Supervisor Router]
    
    Supervisor --> AgentRuntime[Canonical AgentRuntime]
    
    subgraph Agent Core
        AgentRuntime --> Und[Understanding]
        AgentRuntime --> Ctx[Context Manager]
        AgentRuntime --> Safe[Safety Filter]
        
        Und --> Decide[Decide]
        Ctx --> Decide
        Safe --> Decide
        
        Decide --> Answer[Answer Pipeline]
        Decide --> Task[Task Pipeline]
        
        Task --> Planner[Planner]
        Planner --> Executor[Executor]
        Executor --> Tools[Tools]
        Tools --> Observer[Observer]
        Observer --> Replanner[Replanner]
        Replanner --> Verify[Verifier]
        Verify --> Task
    end
    
    Agent Core --> Mem[Memory]
    Mem --> PG[(PostgreSQL + pgvector)]
    
    Agent Core --> Outbox[Events / Outbox]
    Outbox --> Redis[(Redis Streams)]
    Redis --> SSE[SSE / WebSocket Server]
    SSE --> Frontend[Frontend UI]
```

## Core Tenets
1. **The LLM Proposes, the App Authorizes**: Tool executions never happen blindly. The `AgentFirewall` explicitly verifies capability bindings.
2. **Canonical Orchestration**: All sub-agents (Researchers, Coders) sit behind the Supervisor but execute logic using the exact same `AgentRuntime` engine.
3. **Data Sovereignty**: The `Privacy API` exposes explicit cascading export and delete pipelines. Semantic Cache arrays are mathematically hashed to a User ID to enforce absolute partition isolation.

