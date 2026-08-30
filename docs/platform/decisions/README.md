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
