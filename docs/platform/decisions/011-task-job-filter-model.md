# ADR 011 — Task, Job & FilterFingerprint Model

- Status: Accepted
- Date: 2026-08-31
- Related: [ADR 006](006-hybrid-incremental-crawl.md), [ADR 007](007-transactional-outbox-celery.md)

## Context

The system must handle many users with overlapping search filters efficiently:

1. One crawl per unique filter (not per user)
2. Fast lookup of users sharing a filter or brand (e.g. all "Benz" subscribers)
3. When a user changes filter criteria, fingerprint syncs immediately and crawl/rematch triggers when stale
4. Beat scheduling prioritizes filters with more enabled users
5. Self-enrichment (global crawl) coexists with user-driven filter crawls

## Decision

### 1. Identity model

| Concept | Field | Role |
|---|---|---|
| Logical crawl unit | `filter_fingerprint` | SHA256 of canonical criteria — stable dedup key |
| Execution instance | `CrawlJob.id` | UUID per run; many runs share one fingerprint |
| Checkpoint namespace | `source_key` | `bama:{section}:filter:{hash[:16]}` in `crawler_state` |

Users with identical criteria share one `FilterCrawlState` row and one active crawl job.

When filter changes → fingerprint recomputed → user moves to new crawl unit; old fingerprint `enabled_search_count` refreshed.

### 2. Task taxonomy

| Family | Celery tasks | Queue | Idempotency |
|---|---|---|---|
| Crawl | `crawl.scheduled_tick`, `crawl.on_demand`, `crawl.site_map` | `filter` / `crawl` | `idempotency_key` + fingerprint dedup |
| Match | `match.process_ad` | `match` | `UNIQUE(ad_id, search_id)` |
| Notify | `notify.orchestrate` | `notify` | `UNIQUE(match_id, channel)` |

Outbox relay (ADR 007) remains sole entry to match/notify pipelines.

### 3. Two-tier data enrichment

| Tier | Job type | Purpose | Priority |
|---|---|---|---|
| T0 | `SITE_MAP`, taxonomy sync | Discover brands/models/URLs | Background |
| T1 | `SCHEDULED_INCREMENTAL` | Global `/car` baseline cache | Low |
| T2 | `ON_DEMAND_FILTER` + beat | Per-filter incremental; deduped | **High** — user-count priority |
| T3 | `POST /searches`, `/refresh?force=true` | User-triggered immediate fetch | Highest |

Single source of truth: `advertisements` table. All tiers write there; match reads with SQL pre-filter.

### 4. Scheduling priority

Beat selects stale active fingerprints ordered by:

1. `enabled_search_count DESC` — more users = higher priority
2. `last_crawl_at ASC NULLS FIRST` — oldest within same user count

Budget: `CRAWL_BEAT_FILTER_LIMIT` (default 20) filter jobs per tick. Global incremental runs after filter batch in `scheduled_tick`.

### 5. Index strategy (searches)

| Index | Columns | Use |
|---|---|---|
| `ix_searches_fingerprint_enabled` | `filter_fingerprint`, `enabled` | Users sharing exact filter |
| `ix_searches_brand_term_enabled` | `brand_term_id`, `enabled` | Taxonomy-backed brand lookup |
| `ix_searches_brand_enabled` | `brand`, `enabled` | Label fallback (e.g. "بنز") |

### 6. Filter update sync

`PUT /api/searches/{id}` when filter fields change:

1. Recompute `filter_fingerprint` via `FilterCrawlService.prepare_search`
2. Enqueue `ON_DEMAND_FILTER` if new fingerprint cache is stale
3. Dispatch job; rematch existing ads when cache sufficient
4. Return `filter_fingerprint`, `job_id`, `is_crawling` (mirror create response)

### 7. Matching pre-filter

`MatchingService.process_new_ad` must not load all enabled searches. Use SQL pre-filter via `search_filter.sql_*` helpers on brand, model, year, price, mileage, location before Python confirmation.

## Consequences

| ✅ | ❌ |
|---|---|
| O(users) crawls → O(unique filters) | Exact fingerprint only — no brand-level crawl coalescing yet |
| Indexed user lookup by filter/brand | More indexes on searches table |
| User-count-aware beat fairness | High-count filters may starve low-count if budget full |
| Filter change triggers immediate sync | Extra crawl jobs on frequent filter edits |

## Rejected Alternatives

| Option | Why rejected |
|---|---|
| `job_id = fingerprint` | Conflates run instance with logical unit; breaks audit trail |
| Brand-level crawl coalescing | Changes checkpoint semantics; defer until fingerprint count explodes |
| Full-table scan matching | Does not scale with user count |

## Related

- [006-hybrid-incremental-crawl.md](006-hybrid-incremental-crawl.md)
- [007-transactional-outbox-celery.md](007-transactional-outbox-celery.md)
