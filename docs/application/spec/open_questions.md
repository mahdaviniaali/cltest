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
| OQ-004 | Rate limiting / robots.txt policy for Bama.ir | platform | ✅ crawl | platform | open |
| OQ-005 | Async model: queue vs in-process scheduler | platform | ✅ approach | platform | open |
| OQ-006 | Notification channel اول: Email, Telegram, Webhook, …? | application | ✅ approach | application | open |
| OQ-009 | K8s topology: single deployment vs split services | infra | ✅ deploy | shared | open |
| OQ-010 | Observability stack: logs, metrics, tracing | infra | ❌ | shared | open |

## Closed Questions

| ID | Question | Resolution | Link |
|---|---|---|---|
| OQ-001 | Target site production crawl | Bama.ir — car advertisements | [`base/تعریف_پروژه.md`](../../base/تعریف_پروژه.md) |
| OQ-007 | Database: relational vs document vs other | Relational DB (SQLite dev / PostgreSQL prod) + manual schema — no entity auto-detection | [`platform/decisions/005-relational-db-manual-schema.md`](../../platform/decisions/005-relational-db-manual-schema.md) |
| OQ-008 | Dedup key strategy when Bama has no stable ID | `bama_id` — UNIQUE constraint on Bama ad number | [`application/spec/schema/advertisements.md`](schema/advertisements.md) |

## Close Protocol

1. Decision → ADR or capability doc
2. Update Status → `closed`
3. Add Resolution link
4. If blocking → update [`product_blueprint.md`](product_blueprint.md)
