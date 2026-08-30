# Application Architecture Overview

```yaml
---
domain: application
authority: L2
owner: application-architecture
not_authoritative_for:
  - platform internals (→ platform/architecture/)
---
```

## System Map

```
┌─────────────┐     (planned)      ┌──────────────┐
│  frontend/  │ ─ ─ ─ ─ ─ ─ ─ ─ ▶ │  API layer   │
└─────────────┘                    │  (not built) │
                                   └──────┬───────┘
                                          │
┌─────────────┐                           │
│  main.py    │ ─── uses ────────────────▼
│  *Crawler   │              Platform (crawler core)
└─────────────┘
        │
        ▼
   project/data/*.json
```

## Current Composition

`main.py` = **composition root**:

- reads config from platform settings
- instantiates platform components
- wires `ExampleCrawler` as active implementation

## Planned Layers (not implemented)

| Layer | Status |
|---|---|
| REST/GraphQL API | ❌ |
| Job queue / scheduler | ❌ |
| Frontend data fetch | ❌ |

> Planned items live in [`knowledge/`](../knowledge/) — not L1.

## Cross-Domain Rule

Application docs **link to** platform L1 for API facts — no duplicate.
