# Phase 89: Agent Learning Loop

NOVA strictly prohibits autonomous code mutation or prompt rewriting to prevent cascading degradation or hostile takeover.

The formal learning loop is:
1. **Feedback Collection**: Thumb up/down and text feedback collected via the UI.
2. **Failure Classification**: Feedback is clustered (e.g., "Hallucinated API route", "Wrong tool selected").
3. **Evaluation Dataset**: Failed traces are converted into `TestCase` objects and added to the regression suite.
4. **Engineering Review**: Human engineers adjust the PromptRegistry or Tool descriptions.
5. **Benchmark**: `scripts/run_benchmarks.py` validates the fix without regressing other skills.

---

# Phase 90: Production Canary System

NOVA relies on NGINX / Kubernetes traffic shaping to deploy new versions safely.

### Rollout Strategy
- **1% Traffic**: Validates that the container boots, API connects to DB, and basic `/live` probes succeed.
- **5% Traffic**: Validates integration boundaries and basic LLM routing.
- **25% Traffic**: Triggers statistically significant load. The `AgentEvaluator` actively samples 1 in 10 requests to grade safety and hallucination.
- **50% Traffic**: Full cache warming.
- **100% Traffic**: Stable promotion.

### Promotion Gate
A version is only promoted to the next tier if:
- `NOVA Agent Score` >= Baseline.
- `Safety Violations` == 0.
- `P90 Latency` < 1.5s.
- `5xx Error Rate` < 0.1%.

