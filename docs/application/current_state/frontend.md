# Application Frontend

```yaml
---
domain: application
authority: L1
owner: frontend
verify: frontend/
questions:
  - What is the current state of the frontend?
not_authoritative_for:
  - planned UI (→ knowledge/)
---
```

## Status

| Item | State |
|---|---|
| Framework | ❌ not selected |
| Build tool | ❌ not configured |
| API integration | ❌ not implemented |

## Existing Files

| File | Content |
|---|---|
| `frontend/package.json` | scaffold, placeholder scripts |
| `frontend/README.md` | placeholder readme |

## package.json Scripts

| Script | Behavior |
|---|---|
| `dev` | echo placeholder message |
| `build` | echo placeholder message |

## package.json Metadata

| Field | Value |
|---|---|
| name | `crawler-frontend` |
| version | `0.1.0` |
| private | `true` |

## Backend Connection

هیچ endpoint HTTP یا WebSocket بین frontend و crawler **وجود ندارد**.
