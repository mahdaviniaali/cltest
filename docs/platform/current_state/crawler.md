# Platform Crawler — Current State

```yaml
---
domain: platform
authority: L1
owner: crawler-runtime
verify: project/src/crawler/
---
```

## Architecture

Hybrid incremental crawler (ADR 006) with hexagonal ports:

| Layer | Path |
|---|---|
| Domain ports | `crawler/domain/ports.py`, `entities.py` |
| Application | `crawler/application/incremental_crawl.py`, `filter_incremental_crawl.py`, `filter_listing_url_builder.py`, `on_demand_crawl.py`, `site_map_crawl.py`, `site_map_projection_builder.py`, `crawl_job_runner.py` |
| Domain | `crawler/domain/url_identity.py`, `crawl_policy.py`, `robots.py`, `url_patterns.py`, `link_scorer.py` |
| Adapters | `crawler/adapters/bama/parsers.py`, `page_classifier.py`, `link_extractor.py`, `http_page_fetcher.py`, `db_ad_store.py` |

## Crawl modes

| Mode | Trigger | Celery task |
|---|---|---|
| Scheduled tick | Beat every `CRAWL_INTERVAL_SECONDS` | `crawl.scheduled_tick` → filter crawls first, then global |
| Filter incremental | Search create/refresh, Beat stale filters | `crawl.on_demand` → `ON_DEMAND_FILTER` (queue `filter`) |
| Scheduled global incremental | Beat (after filter tick) | `crawl.scheduled_incremental` via tick |
| On-demand global | API `/api/crawl/refresh` | `crawl.on_demand` → `ON_DEMAND_GLOBAL` |
| Site map BFS | Inspector `/api/inspector/site-map/start` | `crawl.site_map` |

## Site map (ADR 008, ADR 009)

1. Each Inspector run targets up to `max_pages` **new** URLs (UI default 500); prior `visited_urls` are skipped
2. Fresh job always bootstraps `section_roots` + sitemap frontier even when home was crawled before
3. Level-first BFS: `heapq` with `sort_key = (depth, -weight, seq)` — weights from `route_rules` / `section_roots` in `bama_site.yaml`
4. Discovered-but-uncrawled URLs persisted as `site_nodes.status=discovered` and re-queued on next run
5. Sitemap capped on first run (`sitemap_max_urls`); incremental runs seed more unvisited sitemap URLs (up to `max_pages × 3`)
6. Canonical URL dedup via configurable `strip_query_params`
7. Config-driven page roles (`section_hub`, `model_hub`, `ad_detail`, …) — no ad parsing in site map loop
8. Persist graph (`site_nodes`, `site_edges`) + events (`level_completed`, `page_fetched`)
9. Build section catalog (`site_sections`) on completion for incremental crawl routing
10. Build aggregated site map projection (`site_map_groups`) — hierarchical groups with `page_count` and `weight`; Inspector reads via `GET /api/inspector/site/map` (no per-request aggregation)
11. Build taxonomy catalog (`taxonomy_terms`, `taxonomy_refs`) via `TaxonomyBuilder` — brands at depth 2, models at depth 3 per vehicle section (`car`, `motorcycle`, `truck`)

## Incremental logic

1. Load checkpoint `crawler_state.last_seen_bama_id`
2. Parse Bama listing pages (newest first)
3. Stop when checkpoint reached or `CRAWL_MAX_PAGES`
4. Fetch detail → `DbAdStore` (ad + outbox in one TX)
5. Update checkpoint

## Config (env)

| Variable | Default |
|---|---|
| `BAMA_LISTING_URL` | `https://bama.ir/car` |
| `CRAWL_INTERVAL_SECONDS` | `300` |
| `CRAWL_MAX_PAGES` | `10` |
| `CRAWL_DELAY_SECONDS` | `1.0` |
| `CRAWL_STALENESS_SECONDS` | `300` |
| `SITE_MAP_MAX_PAGES` | `5000` |
| `SITE_MAP_MAX_DEPTH` | `6` |
| `SITE_MAP_DELAY_SECONDS` | `1.0` |

## Workers

```bash
celery -A app.workers.celery_app worker -Q filter,crawl,outbox_relay,match,notify -l info
celery -A app.workers.celery_app beat -l info
```

Run from `project/` with `PYTHONPATH=src:.`
