# Deployment Pipeline (Phase 78) & Canary Release (Phase 79)

## 1. Staging Environment & Promotion (Phase 78)

NOVA must never be promoted to production directly from a local workstation. The pipeline strictly enforces:

`Local Dev` -> `Staging` -> `Production`

### CI/CD Progression Gates
1. **Migration Test**: Staging database must successfully apply Alembic migrations against a sanitized copy of production data.
2. **Integration Tests**: Executes `test_e2e_full_flow.py` against Staging.
3. **Security Audits**: Trivy, Bandit, and Safety must pass with zero criticals.
4. **Agent Evaluations**: `real_evaluator.py` must score > 0.90 on intent accuracy for a core set of 100 benchmark queries.
5. **Load Tests**: Locust `load_tests/locustfile.py` must run with 50 concurrent virtual users for 10 minutes without exceeding the P95 latency bounds (3 seconds).

## 2. AI Canary Release Configuration (Phase 79)

To mitigate LLM hallucinations or regression when rolling out new Ollama models or updated system prompts, we utilize a Canary Release strategy.

### Routing Logic (NGINX / Envoy)
- We deploy `nova-backend-vNext` alongside `nova-backend-stable`.
- NGINX is configured to split traffic using `split_clients`:
  - 95% -> `nova-backend-stable`
  - 5% -> `nova-backend-vNext`

### Automated Evaluation Metrics (The "Canary Judge")
During the canary period (e.g., 2 hours), Prometheus tracks:
- **Task Success Rate**
- **Tool Error Rate**
- **Safety / Hallucination Rate** (Sampled asynchronously via `AgentEvaluator`)
- **Latency / Token generation speed**

### Rollback Triggers
If the canary pod exceeds a 5% error rate or the P90 latency spikes > 2.5s, the CI/CD pipeline immediately issues a web-hook to scale `vNext` to 0 and shift 100% traffic back to `stable`.

