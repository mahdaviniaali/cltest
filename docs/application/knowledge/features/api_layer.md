# Feature — API Layer

```yaml
---
domain: application
authority: L5
maturity: working
owner: feature-api
not_authoritative_for:
  - existing runtime (none built)
---
```

## Status

**Not implemented** — definition only.

## Job

Expose crawl results and trigger jobs from frontend.

## Draft Input/Output

| Endpoint (draft) | Method | Purpose |
|---|---|---|
| `/api/crawls` | GET | list crawl runs |
| `/api/crawls` | POST | trigger crawl |
| `/api/crawls/{id}` | GET | single result |

## Blockers

- OQ-003 API design
- OQ-002 frontend framework

## Promotion Checklist

- [ ] ADR for API framework
- [ ] L1 `application/current_state/api.md`
- [ ] Implementation + tests
- [ ] Update blueprint phase gate
