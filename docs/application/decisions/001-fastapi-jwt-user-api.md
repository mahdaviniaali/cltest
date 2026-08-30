# ADR 006 — FastAPI + JWT Auth for User API

- Status: Accepted
- Date: 2026-08-30
- Closes: partial [OQ-003](../../application/spec/open_questions.md)

## Context

Phase 2 requires REST API for user search/filter CRUD and a frontend consumer. Auth model was TBD (UC-U1).

## Decision

- **FastAPI** + **uvicorn** for HTTP API (`project/run_api.py`)
- **JWT bearer** auth (email in `sub`, bcrypt passwords)
- Routes under `/api/auth/*` and `/api/searches/*`
- **React + Vite** frontend with proxy to backend

## Consequences

| ✅ | ❌ |
|---|---|
| OpenAPI docs auto-generated | JWT secret must be set in production |
| Matches Python stack | Refresh tokens not in MVP |
| CORS configured for local dev | OAuth/social login deferred |

## Related

- [`schema/users_searches.md`](../../application/spec/schema/users_searches.md)
