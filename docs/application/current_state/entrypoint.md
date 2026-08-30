# Application Entrypoint

```yaml
---
domain: application
authority: L1
owner: entrypoint
verify: project/main.py
questions:
  - How is the crawler application started and wired?
not_authoritative_for:
  - platform class internals
---
```

## Entry File

`project/main.py`

## Bootstrap Sequence

| Step | Action |
|---|---|
| 1 | `sys.path.insert` → `project/src` |
| 2 | `setup_logging()` |
| 3 | Define URL list (hardcoded) |
| 4 | Create `HttpClient(settings.USER_AGENT, settings.TIMEOUT)` |
| 5 | Create `ExampleCrawler(client, delay=settings.DELAY)` |
| 6 | `crawler.crawl(urls)` |
| 7 | `JsonStorage(settings.OUTPUT_DIR).save(results, filename="crawl")` |
| 8 | `client.close()` in `finally` |

## Current URL List

| URL |
|---|
| `https://example.com` |

## Active Crawler

| Class | Module |
|---|---|
| `ExampleCrawler` | `crawler.example_crawler` |

## Run Command

```bash
cd project && python main.py
```

## Output

JSON file in `settings.OUTPUT_DIR` with prefix `crawl_`.
