# ADR 007 — Transactional Outbox + Celery Queues

- Status: Accepted
- Date: 2026-08-30
- Closes: [OQ-005](../../application/spec/open_questions.md)
- Related: [ADR 006](006-hybrid-incremental-crawl.md)

## Context

New ads must trigger matching and notifications without losing events if a worker crashes mid-pipeline. The crawler persists ads; downstream match/notify must be **reliable** and **decoupled**.

OQ-005 asked: queue vs in-process scheduler.

## Decision

### 1. Transactional outbox

When a **new** advertisement is inserted, in the **same DB transaction**:

```text
INSERT advertisement
INSERT outbox_events (event_type=ad.created, status=PENDING)
COMMIT
```

Relay worker polls `outbox_events`, dispatches to match queue, marks `DONE` on success. Failed rows retry with backoff.

At-least-once delivery; match/notify handlers must be idempotent (`UNIQUE(ad_id, search_id)` on matches).

### 2. Celery + Redis

| Component | Role |
|---|---|
| Redis | Celery broker + result backend (optional) |
| Celery Beat | Scheduled incremental crawl (every `CRAWL_INTERVAL_SECONDS`) |
| Celery workers | Process task queues |

**PostgreSQL/SQLite** remains source of truth for ads, jobs, checkpoint, outbox.

### 3. Queues

| Queue | Tasks | Concurrency |
|---|---|---|
| `crawl` | `crawl.scheduled_incremental`, `crawl.on_demand` | 1 |
| `outbox_relay` | `outbox.relay` | 1 |
| `match` | `match.process_ad` | N |
| `notify` | `notify.send` | N |

### 4. Job table `crawl_jobs`

Tracks crawl runs: type, status, metrics, `idempotency_key` UNIQUE. Beat skips new scheduled job if one is `RUNNING`.

### 5. Dev vs prod

| Env | Broker |
|---|---|
| Dev | Redis local (`redis://localhost:6379/0`) |
| Prod | Redis service (K8s Deployment) |

Workers run as separate process: `celery -A app.workers.celery_app worker`

## Consequences

| ✅ | ❌ |
|---|---|
| No lost ad.created events | Extra infra (Redis) |
| K8s-ready (api / worker / beat split) | At-least-once → idempotency required |
| Decoupled crawl vs match vs notify | Operational complexity vs monolith |

## Rejected Alternatives

| Option | Why rejected |
|---|---|
| In-process only | No horizontal scale; lost events on crash |
| Direct Celery publish on save | Dual-write problem if DB commits but broker fails |
| DB polling only (no Celery) | Works for MVP but weaker retry/routing; Celery chosen for K8s path |

## Related

- [006-hybrid-incremental-crawl.md](006-hybrid-incremental-crawl.md)
- [005-relational-db-manual-schema.md](005-relational-db-manual-schema.md)
