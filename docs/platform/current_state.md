# Platform — Current State Index

```yaml
---
domain: platform
authority: L1
owner: platform-index
verify: project/src/crawler/
not_authoritative_for:
  - why (→ decisions/)
  - tutorial (→ architecture/)
---
```

## Topics

| Topic | Owner | verify |
|---|---|---|
| Modules & classes | [`current_state/modules.md`](current_state/modules.md) | `project/src/crawler/` |
| Config & env vars | [`current_state/config.md`](current_state/config.md) | `project/config/settings.py` |
| Storage contract | [`current_state/storage.md`](current_state/storage.md) | `project/src/crawler/storage/` |
| Dependencies | [`current_state/dependencies.md`](current_state/dependencies.md) | `project/requirements.txt` |

## Public API Surface

| Component | Module | Role |
|---|---|---|
| `BaseCrawler` | `crawler.core.base_crawler` | abstract crawl loop |
| `HttpClient` | `crawler.core.http_client` | HTTP + retry |
| `HtmlParser` | `crawler.parsers.html_parser` | HTML extraction |
| `JsonStorage` | `crawler.storage.json_storage` | persist results |

## L2 References

- [`architecture/overview.md`](architecture/overview.md)
- [`decisions/README.md`](decisions/README.md)
