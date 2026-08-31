# Application Persistence

```yaml
---
domain: application
authority: L1
owner: persistence
verify: project/src/app/models/
questions:
  - How are advertisements, users, and searches stored?
  - What is the dedup key for ads?
not_authoritative_for:
  - why relational DB (→ platform/decisions/005)
  - draft schema rationale (→ spec/schema/)
---
```

## Database

| Property | Value |
|---|---|
| ORM | SQLAlchemy 2.x |
| Dev default | SQLite `data/app.db` |
| Config | `settings.DATABASE_URL` |
| Init script | `python scripts/init_db.py` |
| Inspect data | `python scripts/inspect_data.py` |
| Stale job cleanup | `python scripts/cleanup_stale_jobs.py` |
| Scripts policy | [`development/scripts.md`](../../development/scripts.md) |

## Tables

| Table | Model | Dedup / Key |
|---|---|---|
| `advertisements` | `app.models.advertisement.Advertisement` | UNIQUE `bama_id` |
| `users` | `app.models.user.User` | UNIQUE `email` |
| `searches` | `app.models.search.Search` | FK `user_id` → users; indexes on `filter_fingerprint`, `(filter_fingerprint, enabled)`, `(brand_term_id, enabled)`, `(brand, enabled)` |
| `filter_crawl_states` | `app.models.filter_crawl_state.FilterCrawlState` | PK `fingerprint` — shared per-filter checkpoint + freshness |
| `crawler_state` | `app.models.crawler_state.CrawlerState` | PK `source_key` (global + per-filter via `bama:{section}:filter:{hash}`) |
| `crawl_jobs` | `app.models.crawl_job.CrawlJob` | UNIQUE `idempotency_key` |
| `outbox_events` | `app.models.outbox_event.OutboxEvent` | — |
| `matches` | `app.models.match.Match` | UNIQUE `(ad_id, search_id)` |
| `notifications` | `app.models.notification.Notification` | UNIQUE `(match_id, channel)` — inbox fields: title, body, payload, read_at |
| `taxonomy_snapshots` | `app.models.taxonomy.TaxonomySnapshot` | versioned site-map extractions |
| `taxonomy_terms` | `app.models.taxonomy.TaxonomyTerm` | brand/model/city catalog |
| `taxonomy_refs` | `app.models.taxonomy.TaxonomyRef` | evidence URLs per term |
| `search_bootstrap_metrics` | `app.models.taxonomy.SearchBootstrapMetric` | per-bootstrap discovery log |

## Transactional outbox

New ads: `DbAdStore.save_new` inserts ad + `outbox_events` (`ad.created`) in one commit. Relay task dispatches to match queue.

## Repositories

| Class | Module |
|---|---|
| `AdvertisementRepository` | `app.repositories.advertisement_repository` |
| `UserRepository` | `app.repositories.user_repository` |
| `SearchRepository` | `app.repositories.search_repository` |
| `CrawlJobRepository` | `app.repositories.crawl_job_repository` |
| `FilterCrawlStateRepository` | `app.repositories.filter_crawl_state_repository` |
| `CrawlerStateRepository` | `app.repositories.crawler_state_repository` |
| `OutboxRepository` | `app.repositories.outbox_repository` |

## Unit of Work

`app.db.unit_of_work.UnitOfWork` — shared session commit/rollback for multi-step writes.

### SearchRepository methods

| Method | Behavior |
|---|---|
| `list_for_user(user_id)` | all searches for user |
| `get_for_user(user_id, search_id)` | single owned search |
| `create(user_id, data)` | new filter |
| `update(search, data)` | patch fields |
| `delete(search)` | remove |
| `toggle_enabled(search)` | flip enabled flag |
| `list_enabled_by_fingerprint(fingerprint)` | enabled searches sharing exact filter (ADR-011) |
| `list_enabled_by_brand_term(brand_term_id)` | enabled searches for taxonomy brand |
| `list_enabled_by_brand(brand)` | enabled searches by brand label |
| `list_candidates_for_ad(ad)` | SQL pre-filter for matching |

## Beat scheduling (ADR-011)

Stale active fingerprints enqueued by Celery Beat ordered by `enabled_search_count DESC`, then oldest `last_crawl_at`. Budget: `CRAWL_BEAT_FILTER_LIMIT` (default 20) per tick.

## API Entry

| Property | Value |
|---|---|
| Run | `python run_api.py` |
| App module | `app.api.main:app` |
| Port | `8000` |
| Auth | JWT bearer |

## Env

| Variable | Default |
|---|---|
| `DATABASE_URL` | `sqlite:///data/app.db` |
| `JWT_SECRET_KEY` | dev placeholder |
| `CORS_ORIGINS` | `http://localhost:5173` |
| `CRAWL_BEAT_FILTER_LIMIT` | `20` |
