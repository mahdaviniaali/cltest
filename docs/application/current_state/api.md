# Application API — Current State

```yaml
---
domain: application
authority: L1
owner: api-surface
verify: project/src/app/api/
---
```

## Run

```bash
python run_api.py
```

Default: `http://127.0.0.1:8000`

## Routes

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | no | liveness |
| POST | `/api/auth/register` | no | register |
| POST | `/api/auth/login` | no | login |
| GET | `/api/auth/me` | JWT | current user |
| CRUD | `/api/searches/*` | JWT | filter CRUD |
| GET | `/api/searches/{id}/results` | JWT | cached ads for saved filter |
| POST | `/api/ads/preview` | JWT | live preview by filter criteria |
| GET | `/api/ads` | JWT | list all ads |
| GET | `/api/ads/{bama_id}` | JWT | ad detail |
| POST | `/api/crawl/refresh` | JWT | global refresh (neutral 202) |
| GET | `/api/data/status` | JWT | `last_updated_at` + `is_refreshing` |
| POST | `/api/crawl/trigger` | JWT | legacy admin trigger (prefer refresh) |
| GET | `/api/crawl/jobs/{id}` | JWT | internal job detail |
| GET | `/api/crawl/status` | JWT | internal crawl status |

## Cache-first UX contract

- `POST /api/searches` — **only saves** filter; does not auto-crawl
- `POST /api/ads/preview` — returns global cache matching criteria + `last_updated_at`
- `POST /api/crawl/refresh` — always returns `{ is_refreshing, message }` without job_id
- If crawl already running → same neutral response (no new job)

## Frontend routes

| Path | Page |
|---|---|
| `/` | Dashboard — filter CRUD + live preview in form |
| `/searches/:id` | Saved filter results + refresh |
