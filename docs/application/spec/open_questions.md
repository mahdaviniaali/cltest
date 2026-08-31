# Open Questions Register

```yaml
---
domain: application
authority: L5
owner: open-questions
not_authoritative_for:
  - resolved facts (→ current_state/ or ADR)
---
```

## Active Questions

| ID | Question | Owner | Blocking? | Domain | Status |
|---|---|---|---|---|---|
| OQ-002 | Frontend لازم است یا API-only کافی است؟ | product | ❌ | application | open |
| OQ-003 | API design: REST shape, auth, versioning | platform+app | ✅ approach | shared | open |
| OQ-010 | Observability stack: logs, metrics, tracing | infra | ❌ | shared | open |

## Closed Questions

| ID | Question | Resolution | Link |
|---|---|---|---|
| OQ-006 | Notification channel اول | in_app primary + extensible ports | [ADR-010](../../platform/decisions/010-extensible-notification-channels.md) |
| OQ-009 | K8s topology | Split: api / worker / beat / redis | [`k8s/cltest.yaml`](../../../k8s/cltest.yaml), ADR-007 |
| OQ-001 | Target site production crawl | Bama.ir — car advertisements | [`base/تعریف_پروژه.md`](../../base/تعریف_پروژه.md) |
| OQ-007 | Database: relational vs document vs other | Relational DB (SQLite dev / PostgreSQL prod) + manual schema — no entity auto-detection | [`platform/decisions/005-relational-db-manual-schema.md`](../../platform/decisions/005-relational-db-manual-schema.md) |
| OQ-008 | Dedup key strategy when Bama has no stable ID | `bama_id` — UNIQUE constraint on Bama ad number | [`application/spec/schema/advertisements.md`](schema/advertisements.md) |
| OQ-004 | Rate limiting / robots.txt policy for Bama.ir | Respect robots.txt; delay between pages; crawl concurrency 1; HttpClient retry | [`platform/decisions/006-hybrid-incremental-crawl.md`](../../platform/decisions/006-hybrid-incremental-crawl.md) |
| OQ-005 | Async model: queue vs in-process scheduler | Celery + Redis broker; PostgreSQL outbox + job state | [`platform/decisions/007-transactional-outbox-celery.md`](../../platform/decisions/007-transactional-outbox-celery.md) |

## Close Protocol

1. Decision → ADR or capability doc
2. Update Status → `closed`
3. Add Resolution link
4. If blocking → update [`product_blueprint.md`](product_blueprint.md)
