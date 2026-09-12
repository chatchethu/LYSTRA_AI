# Disaster Recovery Drill (Phase 103)

## Objective
Simulate a total availability zone collapse and restore the NOVA environment from scratch using automated scripts.

## Drill Steps
1. Destroy staging PostgreSQL container and Redis container.
2. Destroy localized object storage (`UPLOAD_DIR`).
3. Run `scripts/restore.ps1`.
4. Validate vector dimension integrity in pgvector.
5. Validate user JWTs still authenticate.

## Target Metrics
- **Recovery Time Objective (RTO)**: < 15 minutes.
- **Recovery Point Objective (RPO)**: < 5 minutes (WAL shipping granularity).

