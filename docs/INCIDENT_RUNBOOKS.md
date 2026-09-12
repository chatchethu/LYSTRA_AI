# Production Incident Runbooks (Phase 102)

## 1. LLM Outage / Hallucination Spike
**Detect**: OTLP metrics show P90 Latency > 5s or Evaluation Score drops below 85%.
**Contain**: `AIReleaseController` automatically scales the canary to 0 or routes to fallback cloud model.
**Investigate**: Check `ollama` container logs and GPU VRAM usage.
**Recover**: Restart Ollama service; flush KV cache.

## 2. PostgreSQL Outage
**Detect**: Health probe `/ready` returns 503; SQLAlchemy throws `ConnectionRefused`.
**Contain**: Web app enters Read-Only / Graceful degradation mode (returning 503).
**Investigate**: Check `pg_stat_activity` and disk space.
**Recover**: Execute `restore.ps1` from latest WAL backup if data corruption occurred.

## 3. Redis Outage
**Detect**: Celery tasks hang in pending; Rate Limiting drops open.
**Contain**: FastAPI automatically bypasses rate-limiting or caches locally (Chaos Test validated).
**Investigate**: Check Redis memory fragmentation.
**Recover**: Restart Redis; it operates statelessly for caching/queues.

## 4. Security Incident / SSRF Breach Attempt
**Detect**: Splunk/Grafana alerts on high volume of `SSRFViolationError`.
**Contain**: WAF automatically bans the offending source IP.
**Investigate**: Review Trace Viewer (Phase 84) to determine which tool invoked the URL.
**Recover**: Update `ssrf_check.py` to ban the targeted subnet.

