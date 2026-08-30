# Platform Architecture Overview

```yaml
---
domain: platform
authority: L2
owner: architecture
not_authoritative_for:
  - canonical API values (→ current_state/)
  - decision rationale (→ decisions/)
---
```

## Layer Diagram

```
Application (main.py, *Crawler)
        │
        ▼
┌───────────────────────────────────┐
│  BaseCrawler.crawl()              │
│    ├── HttpClient.get()           │
│    ├── subclass.parse()           │
│    └── delay sleep                │
└───────────────────────────────────┘
        │
        ▼
┌─────────────┐  ┌─────────────┐
│ HtmlParser  │  │ JsonStorage │
└─────────────┘  └─────────────┘
```

## Data Flow

1. Caller passes URL list to `BaseCrawler.crawl()`
2. For each URL: `HttpClient.get()` → HTML string
3. `parse(url, html)` → structured record (subclass-defined)
4. Results collected in `self.results`
5. Caller persists via `JsonStorage.save()`

## Extension Points

| Extend | How |
|---|---|
| New site crawler | subclass `BaseCrawler`, implement `parse()` |
| New parser | add module under `parsers/` |
| New storage | add module under `storage/` |

## Config Bootstrap

`config/settings.py` loads `.env` at import — consumed by application layer.

## Boundaries

- Platform **does not** know about specific target sites (except `ExampleCrawler` as sample)
- Platform **does not** expose HTTP server or CLI framework

## Hexagonal Model

معماری **Ports & Adapters** — crawl tools (Scrapy, Crawl4AI, requests+BS4) در لایه infrastructure هستند و به domain گره نمی‌خورند.

→ جزئیات: [`hexagonal_crawl_tools.md`](hexagonal_crawl_tools.md) · ADR: [`decisions/004-scrapy-crawl4ai-crawl-tools.md`](../decisions/004-scrapy-crawl4ai-crawl-tools.md)
