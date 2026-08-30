# Celery Workers — Current State

```yaml
---
domain: platform
authority: L1
owner: workers
verify: project/src/app/workers/
---
```

## Broker

Redis — `CELERY_BROKER_URL` (default `redis://localhost:6379/0`)

## Queues

| Queue | Tasks |
|---|---|
| `crawl` | `crawl.scheduled_incremental`, `crawl.on_demand` |
| `outbox_relay` | `outbox.relay` |
| `match` | `match.process_ad` |
| `notify` | `notify.send` |

## Beat schedule

| Task | Interval |
|---|---|
| `crawl.scheduled_incremental` | `CRAWL_INTERVAL_SECONDS` (300s) |
| `outbox.relay` | 30s |

## App module

`app.workers.celery_app:celery_app`
