# Schema — crawler infrastructure

```yaml
---
domain: application
authority: L5
maturity: working
owner: schema-crawler
source: ADR 006, ADR 007
---
```

## crawler_state

| Column | Type | Notes |
|---|---|---|
| `source_key` | VARCHAR PK | e.g. `bama:car:listings` |
| `last_seen_bama_id` | VARCHAR | incremental stop marker |
| `last_crawl_at` | TIMESTAMPTZ | |
| `last_run_job_id` | VARCHAR FK | → crawl_jobs.id |

## crawl_jobs

| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR PK | UUID |
| `job_type` | VARCHAR | `scheduled_incremental`, `on_demand_search`, `on_demand_global` |
| `status` | VARCHAR | `pending`, `running`, `completed`, `failed`, `cancelled` |
| `triggered_by` | VARCHAR | `beat`, `search:{id}`, `api` |
| `search_id` | INTEGER FK nullable | → searches.id |
| `idempotency_key` | VARCHAR UNIQUE | |
| `pages_crawled`, `ads_found`, `ads_new` | INTEGER | metrics |
| `error` | TEXT | |
| `started_at`, `finished_at`, `created_at` | TIMESTAMPTZ | |

## outbox_events

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `event_type` | VARCHAR | `ad.created`, `notify.requested` |
| `aggregate_id` | VARCHAR | bama_id or match key |
| `payload` | JSON | |
| `status` | VARCHAR | `pending`, `processing`, `done`, `failed` |
| `attempts` | INTEGER | |
| `last_error` | TEXT | |
| `created_at`, `processed_at` | TIMESTAMPTZ | |
