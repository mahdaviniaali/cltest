# Platform Dependencies

```yaml
---
domain: platform
authority: L1
owner: dependencies
verify: project/requirements.txt
questions:
  - What Python packages does the platform require?
not_authoritative_for:
  - why each was chosen (→ decisions/)
---
```

## requirements.txt

| Package | Min Version |
|---|---|
| `requests` | 2.31.0 |
| `beautifulsoup4` | 4.12.0 |
| `lxml` | 5.0.0 |
| `python-dotenv` | 1.0.0 |
| `scrapy` | 2.11.0 |
| `crawl4ai` | 0.4.0 |

## Crawl Infrastructure Tools

Scrapy و Crawl4AI **نصب شده‌اند** — استفاده فقط از طریق **hexagonal adapters** (نه import مستقیم در domain).

| Tool | Role | ADR |
|---|---|---|
| Scrapy | crawl engine adapter (spider, pipeline, retry, concurrency) | [004](../decisions/004-scrapy-crawl4ai-crawl-tools.md) |
| Crawl4AI | browser/render + extraction adapter | [004](../decisions/004-scrapy-crawl4ai-crawl-tools.md) |

→ معماری: [`architecture/hexagonal_crawl_tools.md`](../architecture/hexagonal_crawl_tools.md)

## Usage in Code

| Package | Used by |
|---|---|
| `requests` | `HttpClient` |
| `beautifulsoup4` + `lxml` | `HtmlParser` |
| `python-dotenv` | `config/settings.py` |
| `scrapy` | *(planned)* Scrapy crawl adapter — infrastructure only |
| `crawl4ai` | *(planned)* Crawl4AI fetch/extract adapter — infrastructure only |

## Python Version

3.10+ (type hints, `list[str]` compatible)
