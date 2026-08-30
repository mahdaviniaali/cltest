# Platform Config

```yaml
---
domain: platform
authority: L1
owner: config
verify: project/config/settings.py
questions:
  - What environment variables does the crawler use?
not_authoritative_for:
  - why defaults were chosen
---
```

## Settings Module

| Symbol | Type | Source |
|---|---|---|
| `BASE_DIR` | `Path` | parent of `config/` |
| `DELAY` | `float` | env `CRAWLER_DELAY`, default `1.0` |
| `TIMEOUT` | `int` | env `CRAWLER_TIMEOUT`, default `30` |
| `USER_AGENT` | `str` | env `CRAWLER_USER_AGENT`, see default below |
| `OUTPUT_DIR` | `Path` | env `CRAWLER_OUTPUT_DIR`, default `data/` |
| `DATA_DIR` | `Path` | `BASE_DIR / data` |
| `DATABASE_URL` | `str` | env `DATABASE_URL`, default SQLite `data/app.db` |

## Default USER_AGENT

```
CrawlerBot/1.0 (+https://example.com/bot)
```

## Env File

| File | Purpose |
|---|---|
| `project/.env.example` | template (committed) |
| `project/.env` | local overrides (gitignored) |

## Env Variables

| Variable | Default | Maps to |
|---|---|---|
| `CRAWLER_DELAY` | `1.0` | `settings.DELAY` |
| `CRAWLER_TIMEOUT` | `30` | `settings.TIMEOUT` |
| `CRAWLER_USER_AGENT` | see above | `settings.USER_AGENT` |
| `CRAWLER_OUTPUT_DIR` | `data/` | `settings.OUTPUT_DIR` |
| `DATABASE_URL` | `sqlite:///data/app.db` | `settings.DATABASE_URL` |

## Side Effects on Import

`OUTPUT_DIR.mkdir(parents=True, exist_ok=True)` — directory created at import.
