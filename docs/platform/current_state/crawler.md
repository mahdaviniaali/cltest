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
| Application | `crawler/application/incremental_crawl.py`, `on_demand_crawl.py`, `crawl_job_runner.py` |
| Adapters | `crawler/adapters/bama/parsers.py`, `http_page_fetcher.py`, `db_ad_store.py` |

## Crawl modes

| Mode | Trigger | Celery task |
|---|---|---|
| Scheduled incremental | Beat every `CRAWL_INTERVAL_SECONDS` | `crawl.scheduled_incremental` |
| On-demand | API / search create | `crawl.on_demand` |

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

## Workers

```bash
celery -A app.workers.celery_app worker -Q crawl,outbox_relay,match,notify -l info
celery -A app.workers.celery_app beat -l info
```

Run from `project/` with `PYTHONPATH=src:.`
