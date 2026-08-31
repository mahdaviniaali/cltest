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

Bama.ir New Ads Crawler & Notification System — monitor آگهی‌های جدید، match با فیلتر کاربر، notify.

## Current Phase

**Phase 0 — Scaffold + Definition**

| Deliverable | Status |
|---|---|
| Project definition (Bama task) | ✅ [`base/تعریف_پروژه.md`](../../base/تعریف_پروژه.md) |
| Project approach | ❌ TBD — [`base/رویکرد_پروژه.md`](../../base/رویکرد_پروژه.md) |
| Platform crawler core | ✅ (example.com baseline) |
| Bama crawler | ❌ |
| User/search API | ❌ |
| Matching engine | ❌ |
| Notification (≥1 channel) | ✅ in_app + extensible adapters (ADR-010) |
| Persistence (DB) | ✅ SQLite dev / PostgreSQL prod |
| K8s deployment | ✅ docker-compose + k8s manifests |

## Architecture Locks

| Lock | Rationale |
|---|---|
| Platform/Application split | reuse crawler core |
| L1 as canonical truth | doc-first workflow |
| JSON storage (MVP) | ADR-002 |

## Next Phase Gates

| Gate | Blocker |
|---|---|
| Approach defined | [`base/رویکرد_پروژه.md`](../../base/رویکرد_پروژه.md) — pending architecture session |
| Phase 1 — Bama crawl + dedup | OQ-004, OQ-008 + approach |
| Phase 2 — User API + Matching | OQ-003, OQ-007 |
| Phase 3 — Notification + deploy | OQ-006, OQ-009 |

## Capability Domains (Draft)

| Domain | L0 Status |
|---|---|
| Fetch (Bama) | L0 — example.com baseline only |
| Parse (Bama) | L0 |
| Store (ads) | L0 — JSON scaffold ≠ production DB |
| Dedup | L0 |
| Schedule | L0 |
| User/Search API | L0 |
| Match | L0 |
| Notify | L0 |
| Deploy (K8s) | L0 |

> Capability maturity ≠ existence. See [`knowledge/capabilities/capability_map.md`](../knowledge/capabilities/capability_map.md).
