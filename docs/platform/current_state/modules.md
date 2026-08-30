# Platform Modules

```yaml
---
domain: platform
authority: L1
owner: modules
verify: project/src/crawler/
questions:
  - Which modules and classes exist in the crawler platform?
not_authoritative_for:
  - why
  - application wiring
---
```

## Package Layout

```
project/src/crawler/
├── __init__.py          # version 0.1.0
├── core/
│   ├── base_crawler.py  # BaseCrawler (ABC)
│   └── http_client.py   # HttpClient
├── parsers/
│   └── html_parser.py   # HtmlParser (static methods)
├── storage/
│   └── json_storage.py  # JsonStorage
├── utils/
│   └── logger.py        # setup_logging()
└── example_crawler.py   # ExampleCrawler (sample impl)
```

## Classes

| Class | Type | Public Methods |
|---|---|---|
| `BaseCrawler` | ABC | `crawl(urls)`, `parse(url, html)` abstract |
| `HttpClient` | concrete | `get(url)`, `close()` |
| `HtmlParser` | utility | `extract_title`, `extract_links`, `extract_meta` |
| `JsonStorage` | concrete | `save(data, filename="results")` |
| `ExampleCrawler` | concrete | extends `BaseCrawler` |

## BaseCrawler Behavior

| Property | Value |
|---|---|
| Constructor args | `http_client`, `delay=1.0` |
| `crawl()` | iterates URLs, calls `get()`, then `parse()`, sleeps `delay` |
| Results | accumulated in `self.results: List[Any]` |

## HttpClient Behavior

| Property | Value |
|---|---|
| Constructor args | `user_agent`, `timeout=30`, `max_retries=3` |
| Retry status codes | 429, 500, 502, 503, 504 |
| Backoff factor | 0.5 |
| On failure | logs error, returns `None` |

## HtmlParser Output

| Method | Returns |
|---|---|
| `extract_title(html)` | `Optional[str]` |
| `extract_links(html, base_url="")` | `List[str]` |
| `extract_meta(html)` | `Dict[str, Any]` (name/property → content) |

## ExampleCrawler Output Schema

```json
{
  "url": "string",
  "title": "string | null",
  "meta": { "key": "value" }
}
```
