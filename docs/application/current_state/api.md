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

| Method | Path | Auth |
|---|---|---|
| GET | `/api/health` | no |
| POST | `/api/auth/register` | no |
| POST | `/api/auth/login` | no |
| GET | `/api/auth/me` | JWT |
| CRUD | `/api/searches/*` | JWT |
| GET | `/api/ads` | JWT |
| GET | `/api/ads/{bama_id}` | JWT |
| POST | `/api/crawl/trigger` | JWT → 202 + job_id |
| GET | `/api/crawl/jobs/{id}` | JWT |
| GET | `/api/crawl/status` | JWT |

## Search create side-effect

`POST /api/searches` evaluates cache; if stale, enqueues `crawl.on_demand` Celery task.
