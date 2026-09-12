# Data Retention & Deletion Policy (Phase 66)

This document formalizes the data lifecycle policies for the NOVA AI Agent, encompassing retention limits, automated deletion semantics, and backup behaviors for compliance and privacy standards.

## Retention Periods

| Data Type | Retention Period | Justification |
|-----------|------------------|---------------|
| **Messages & Conversations** | 90 Days | Standard conversational context window. Older conversations are automatically pruned. |
| **Memories (Vectors & LTM)** | 1 Year (Rolling) | Memories expire unless continually accessed or reinforced (Phase 11 decay rules apply). |
| **User Files (Documents/PDFs)** | 30 Days | Transient storage for RAG context. Must be re-uploaded if needed later. |
| **Task History & Plans** | 30 Days | Historical tasks and multi-step plans for audit and replay. |
| **Audit Logs (Tool Approvals)** | 3 Years | Long-term security compliance and risk management. |
| **Telemetry (LLM Tokens/Latency)** | 14 Days | Short-term operational debugging and observability. |
| **Event Streams (SSE/Outbox)** | 7 Days | Short-term replay buffering. |

## Deletion Semantics

### Asynchronous Purging
Deletion is never processed synchronously in the API request path. 
When a user requests deletion, a `delete_user_data_task` (Phase 65) is enqueued in Celery.

### Cascade Behavior
- **Database (PostgreSQL)**: Hard deletes are issued. Cascading foreign keys immediately purge dependent `messages`, `memories`, `documents`, and `tasks`.
- **Vector Database**: pgvector embeddings reside in the `user_memories` and `document_chunks` tables and are purged synchronously with the relational records.
- **Cache (Redis)**: User-bound rate limit counters, session metadata, and cancellation tokens are flushed (`DEL *{user_id}*`).
- **Object Storage (S3/Local)**: Referenced blobs (PDFs, images) are scrubbed.

## Backup Behavior

- **PostgreSQL**: Daily snapshots retained for 30 days. Deletion requests are NOT retroactively applied to immutable backups.
- **Restore Policy**: If a backup is restored, automated scripts purge user records that were marked for deletion between the snapshot date and the restoration date using the Audit Logs.

