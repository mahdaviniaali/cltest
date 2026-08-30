# Platform ADR Index

```yaml
---
domain: platform
authority: L3
owner: decisions-index
not_authoritative_for:
  - current API (→ current_state/)
---
```

## Records

| ID | Title | Status | Date |
|---|---|---|---|
| [001](001-layered-crawler-architecture.md) | Layered crawler architecture | Accepted | 2026-08-30 |
| [002](002-json-storage.md) | JSON file storage | Accepted | 2026-08-30 |
| [003](003-requests-http-client.md) | requests as HTTP client | Accepted | 2026-08-30 |
| [004](004-scrapy-crawl4ai-crawl-tools.md) | Scrapy & Crawl4AI as crawl infrastructure tools | Accepted | 2026-08-30 |
| [005](005-relational-db-manual-schema.md) | Relational DB + manual schema design | Accepted | 2026-08-30 |
| [006](006-hybrid-incremental-crawl.md) | Hybrid incremental crawl + Bama policy | Accepted | 2026-08-30 |
| [007](007-transactional-outbox-celery.md) | Transactional outbox + Celery queues | Accepted | 2026-08-30 |

## Rules

- ADR = **WHY only** — never use as API spec
- Accepted ADR = **immutable** — supersede with new ADR
- Implementation PR → reference ADR number in commit/PR

## When to Write New ADR

- new external dependency
- persistence change
- public contract change
- refactor > 5 files
- boundary/service new
