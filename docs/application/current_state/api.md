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
| GET | `/api/health` | no | liveness (legacy) |
| GET | `/api/health/live` | no | liveness probe |
| GET | `/api/health/ready` | no | readiness (DB + Redis) |
| GET | `/api/metrics` | no | Prometheus text metrics |
| GET | `/api/admin/stats` | JWT | crawl/site stats overview |
| GET | `/api/admin/filter-crawls` | JWT | active filter fingerprints + crawl state |
| GET | `/api/notifications` | JWT | in-app inbox |
| GET | `/api/notifications/unread-count` | JWT | unread badge count |
| PATCH | `/api/notifications/{id}/read` | JWT | mark one read |
| POST | `/api/notifications/read-all` | JWT | mark all read |
| POST | `/api/auth/register` | no | register |
| POST | `/api/auth/login` | no | login |
| GET | `/api/auth/me` | JWT | current user |
| CRUD | `/api/searches/*` | JWT | filter CRUD |
| GET | `/api/searches/{id}/results` | JWT | cached ads for saved filter |
| POST | `/api/searches/{id}/refresh` | JWT | search-scoped bootstrap or incremental handoff |
| POST | `/api/ads/preview` | JWT | live preview by filter criteria |
| GET | `/api/ads` | JWT | list all ads |
| GET | `/api/ads/{bama_id}` | JWT | ad detail |
| POST | `/api/crawl/refresh` | JWT | global refresh (neutral 202) |
| GET | `/api/data/status` | JWT | `last_updated_at` + `is_refreshing` |
| POST | `/api/crawl/trigger` | JWT | legacy admin trigger (prefer refresh) |
| GET | `/api/crawl/jobs/{id}` | JWT | internal job detail |
| GET | `/api/crawl/status` | JWT | internal crawl status |
| POST | `/api/inspector/site-map/start` | JWT | start site map BFS |
| POST | `/api/inspector/jobs/{id}/pause` | JWT | pause site map |
| POST | `/api/inspector/jobs/{id}/resume` | JWT | resume site map |
| POST | `/api/inspector/jobs/{id}/cancel` | JWT | cancel site map |
| GET | `/api/inspector/jobs` | JWT | list site map jobs |
| GET | `/api/inspector/jobs/{id}` | JWT | job status + counters |
| GET | `/api/inspector/jobs/{id}/events` | JWT | crawl events (poll `since_id`) |
| GET | `/api/inspector/site/tree` | JWT | URL path tree |
| GET | `/api/inspector/site/map` | JWT | aggregated site map groups (counts + weights from DB) |
| GET | `/api/inspector/site/graph` | JWT | legacy raw nodes + edges (deprecated) |
| GET | `/api/inspector/site/sections` | JWT | auto-detected sections |
| GET | `/api/inspector/pages/{page_key}` | JWT | page detail |
| GET | `/api/inspector/stats/overview` | JWT | site coverage + taxonomy + crawl health |
| GET | `/api/inspector/stats/searches` | JWT | per-search bootstrap discovery metrics |
| GET | `/api/taxonomy/sections` | JWT | vehicle sections + brand/model counts |
| GET | `/api/taxonomy/brands?section=` | JWT | active brand terms |
| GET | `/api/taxonomy/models?section=&brand_id=` | JWT | models for a brand |
| GET | `/api/taxonomy/cities?section=` | JWT | city terms from ads cache |
| GET | `/api/taxonomy/terms/{id}` | JWT | single taxonomy term |

## Cache-first UX contract

- `POST /api/searches` — saves filter; computes shared `filter_fingerprint`; returns cache when `filter_crawl_states.last_crawl_at` within `CRAWL_STALENESS_SECONDS`, else enqueues `ON_DEMAND_FILTER`; returns `cached_count`, `is_crawling`, `job_id`
- `GET /api/searches/{id}/results` — cached ads + per-filter `last_updated_at`, `bootstrapped`, `cache_sufficient`
- `POST /api/searches/{id}/refresh` — filter-scoped incremental refresh; dedupes by fingerprint; skips when filter cache fresh
- `POST /api/ads/preview` — live preview from cache only (no auto-crawl until save)
- `POST /api/crawl/refresh` — global incremental refresh (neutral 202)
- If crawl already running → same neutral response (no new job)

## Frontend routes

| Path | Page |
|---|---|
| `/` | Dashboard — filter CRUD + live preview in form |
| `/searches/:id` | Saved filter results + refresh |
| `/admin/inspector` | Site map control, tree, aggregated map, live events |
