# ADR 006 — Hybrid Incremental Crawl

- Status: Accepted
- Date: 2026-08-30
- Closes: [OQ-004](../../application/spec/open_questions.md) (partial — crawl policy)
- Related: [ADR 007](007-transactional-outbox-celery.md)

## Context

Bama.ir task requires monitoring **new** car ads — not full-site re-crawl each run. Users need:

1. **Scheduled** background refresh (default every 5 minutes) for a shared ad cache
2. **On-demand** crawl when a user creates a filter and cached data is stale or insufficient

Incremental strategy: start from listing page 1 (newest first), stop when `last_seen_bama_id` checkpoint is reached or `max_pages` exceeded.

## Decision

### 1. Hybrid crawl modes

| Mode | Trigger | Job type |
|---|---|---|
| Scheduled incremental | Celery Beat | `SCHEDULED_INCREMENTAL` |
| On-demand (filter) | `POST /api/searches`, refresh, Beat | `ON_DEMAND_FILTER` |
| On-demand (legacy alias) | — | `ON_DEMAND_SEARCH` → same as filter |
| On-demand (manual global) | `POST /api/crawl/trigger` | `ON_DEMAND_GLOBAL` |

### 2. Checkpoint in PostgreSQL/SQLite (not Redis)

Table `crawler_state`:

- `source_key` PK — e.g. `bama:car:listings`
- `last_seen_bama_id` — stop marker for incremental crawl
- `last_crawl_at`, `last_run_job_id` — audit

Redis is **not** used for checkpoint durability.

### 3. Incremental algorithm

1. Load checkpoint
2. Crawl listing pages from page 1 upward
3. Collect cards until first card `bama_id == last_seen_bama_id` → stop
4. For each new ad: fetch detail → persist (with outbox — ADR 007)
5. Update checkpoint to newest `bama_id` seen

Defaults: `CRAWL_INTERVAL_SECONDS=300`, `CRAWL_MAX_PAGES=10`, `CRAWL_DELAY_SECONDS=1.0`.

### 4. Bama crawl policy (closes OQ-004)

| Rule | Value |
|---|---|
| `robots.txt` | Respect — skip disallowed paths |
| Rate limit | `CRAWL_DELAY_SECONDS` between listing pages; crawl queue concurrency = 1 |
| User-Agent | Identifiable bot string in settings |
| Max pages per run | `CRAWL_MAX_PAGES` (default 10) |
| Retry | Existing `HttpClient` urllib3 retry (429, 5xx) |

No anti-bot bypass. If JS render required → Crawl4AI adapter behind `PageFetcher` port (ADR 004).

### 5. On-demand fast path

When user creates search:

1. Query DB for ads matching filter
2. If count ≥ threshold and data younger than `CRAWL_STALENESS_SECONDS` → return cached
3. Else enqueue **filter incremental** crawl (`ON_DEMAND_FILTER`); API returns job id for polling

### 6. Filter-scoped incremental crawl (2026-08-31 amend)

Bootstrap (`ON_DEMAND_SEARCH` until min count) is **deprecated**. Filters share a canonical **fingerprint** (SHA256 of criteria) and one checkpoint in `filter_crawl_states` + `crawler_state` (`source_key = bama:{section}:filter:{hash}`).

| Phase | Job type | Behavior |
|---|---|---|
| First / stale filter fetch | `ON_DEMAND_FILTER` | Listing URL with Bama query filters + `sort=1`; incremental newest-first until checkpoint or `max_pages` |
| Fresh filter (< `CRAWL_STALENESS_SECONDS`) | — | API returns cached ads; no new job |
| Refresh (same fingerprint) | `ON_DEMAND_FILTER` | Dedupes active PENDING/RUNNING jobs per fingerprint |
| Beat (priority) | `ON_DEMAND_FILTER` | Stale enabled fingerprints before global tick |
| Scheduled global | `SCHEDULED_INCREMENTAL` | Background `/car` incremental (low priority) |

Cache fast-path: `filter_crawl_states.last_crawl_at` within `CRAWL_STALENESS_SECONDS` (default 300s) → sufficient even if ad count < min.

Users A and B with identical criteria → one fingerprint, one checkpoint, one crawl job.

### 7. Legacy bootstrap (removed from runner)

`SearchBootstrapCrawlService` remains for reference; `crawl_job_runner` routes `ON_DEMAND_SEARCH` → filter incremental.

## Consequences

| ✅ | ❌ |
|---|---|
| Low load on Bama — only new ads | Listing sort must stay newest-first (verified in parser spike) |
| Shared cache serves all users | Checkpoint lost if not committed with job completion |
| Clear job traceability via `crawl_jobs` | Two crawl paths to maintain |

## Rejected Alternatives

| Option | Why rejected |
|---|---|
| Full re-crawl each interval | Wasteful; violates task intent |
| Redis-only checkpoint | Lost on restart; no audit trail |
| In-process scheduler only | No scale to K8s worker deployments |

## Related

- [007-transactional-outbox-celery.md](007-transactional-outbox-celery.md)
- [011-task-job-filter-model.md](011-task-job-filter-model.md) — task taxonomy, scheduling priority, index strategy
- [hexagonal_crawl_tools.md](../architecture/hexagonal_crawl_tools.md)
- [open_questions.md](../../application/spec/open_questions.md)
