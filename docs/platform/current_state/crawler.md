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
| Application | `crawler/application/incremental_crawl.py`, `on_demand_crawl.py`, `site_map_crawl.py`, `crawl_job_runner.py` |
| Domain | `crawler/domain/url_identity.py`, `crawl_policy.py`, `robots.py`, `url_patterns.py`, `link_scorer.py` |
| Adapters | `crawler/adapters/bama/parsers.py`, `page_classifier.py`, `link_extractor.py`, `http_page_fetcher.py`, `db_ad_store.py` |

## Crawl modes

| Mode | Trigger | Celery task |
|---|---|---|
| Scheduled incremental | Beat every `CRAWL_INTERVAL_SECONDS` | `crawl.scheduled_incremental` |
| On-demand | API / search create | `crawl.on_demand` |
| Site map BFS | Inspector `/api/inspector/site-map/start` | `crawl.site_map` |
| Search bootstrap | `POST /api/searches` (cache miss) or `POST /api/searches/{id}/refresh` | `crawl.on_demand` → `ON_DEMAND_SEARCH` |

## Site map (ADR 008, ADR 009)

1. Seed homepage only at depth 0; `section_roots` forced at depth 1 after home crawl
2. Level-first BFS: `heapq` with `sort_key = (depth, -weight, seq)` — weights from `route_rules` / `section_roots` in `bama_site.yaml`
3. Sitemap capped (`sitemap_max_urls`); overflow deferred until level 1 completes
4. Canonical URL dedup via configurable `strip_query_params`
5. Config-driven page roles (`section_hub`, `model_hub`, `ad_detail`, …) — no ad parsing in site map loop
6. Persist graph (`site_nodes`, `site_edges`) + events (`level_completed`, `page_fetched`)
7. Build section catalog (`site_sections`) on completion for incremental crawl routing

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
| `CRAWL_STALENESS_SECONDS` | `600` |
| `SITE_MAP_MAX_PAGES` | `5000` |
| `SITE_MAP_MAX_DEPTH` | `6` |
| `SITE_MAP_DELAY_SECONDS` | `1.0` |

## Workers

```bash
celery -A app.workers.celery_app worker -Q crawl,outbox_relay,match,notify -l info
celery -A app.workers.celery_app beat -l info
```

Run from `project/` with `PYTHONPATH=src:.`
