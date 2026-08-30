# Product Blueprint

```yaml
---
domain: application
authority: L5
maturity: working
owner: product-blueprint
not_authoritative_for:
  - runtime facts (→ current_state/)
---
```

## Vision (One Line)

کرالر وب Python با UI برای مشاهده و مدیریت نتایج crawl.

## Current Phase

**Phase 0 — Scaffold**

| Deliverable | Status |
|---|---|
| Platform crawler core | ✅ |
| Example crawl (example.com) | ✅ |
| JSON output | ✅ |
| Layered documentation | ✅ |
| Frontend | ❌ scaffold only |
| API layer | ❌ |
| Production target site | ❌ undefined |

## Architecture Locks

| Lock | Rationale |
|---|---|
| Platform/Application split | reuse crawler core |
| L1 as canonical truth | doc-first workflow |
| JSON storage (MVP) | ADR-002 |

## Next Phase Gates

| Gate | Blocker |
|---|---|
| Phase 1 — First real site | OQ-001 target site |
| Phase 2 — API + Frontend | OQ-002 framework, OQ-003 API design |

## Capability Domains (Draft)

| Domain | L0 Status |
|---|---|
| Fetch | L1 — baseline (HttpClient) |
| Parse | L1 — baseline (HtmlParser) |
| Store | L1 — JSON file |
| Schedule | L0 — not built |
| UI | L0 — scaffold only |

> Capability maturity ≠ existence. See [`knowledge/capabilities/capability_map.md`](../knowledge/capabilities/capability_map.md).
