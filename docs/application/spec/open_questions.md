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
| OQ-001 | کدام سایت target اول production crawl است؟ | product | ✅ Phase 1 | application | open |
| OQ-002 | Frontend framework: React, Vue, or other? | frontend | ✅ Phase 2 | application | open |
| OQ-003 | API layer: REST, CLI-only, or both? | platform+app | ✅ Phase 2 | shared | open |
| OQ-004 | Rate limiting / robots.txt policy? | platform | ❌ | platform | open |
| OQ-005 | Async crawl (concurrent URLs)? | platform | ❌ | platform | open |

## Closed Questions

| ID | Question | Resolution | Link |
|---|---|---|---|
| — | — | — | — |

## Close Protocol

1. Decision → ADR or capability doc
2. Update Status → `closed`
3. Add Resolution link
4. If blocking → update [`product_blueprint.md`](product_blueprint.md)
