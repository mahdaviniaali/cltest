# Platform AI Rules (L4)

```yaml
---
domain: platform
authority: L4
owner: ai-contributor-platform
not_authoritative_for:
  - runtime facts (→ current_state/)
---
```

## Before Editing Platform Code

1. Read [`current_state.md`](../current_state.md) and relevant topic files
2. Read [`development/development_rules.md`](../../development/development_rules.md)
3. Verify claims against code — **no speculation in L1**

## Constraints

- **Do not** add site-specific logic to `core/` — belongs in application crawler
- **Do not** change `BaseCrawler.crawl()` loop without ADR
- **Do not** add HTTP frameworks (FastAPI/Flask) without ADR
- **Do not** duplicate facts — update single L1 owner (A3)
- **Do not** put «planned» features in L1 — use `application/knowledge/`

## When Changing Public API

1. Update L1 owner file in **same PR** (A4)
2. If architectural why changed → new ADR (immutable edit forbidden)
3. If non-obvious → learning report in `application/knowledge/learning_reports/`

## File Placement

| Change | Location |
|---|---|
| HTTP/retry logic | `core/http_client.py` |
| Crawl orchestration | `core/base_crawler.py` |
| HTML extraction | `parsers/` |
| Persistence | `storage/` |
| Sample implementation | `example_crawler.py` or application |

## L1 Update Map

| Change | Update |
|---|---|
| New class/method | `current_state/modules.md` |
| New env var | `current_state/config.md` + `.env.example` |
| New dependency | `current_state/dependencies.md` + `requirements.txt` |
| Storage format change | `current_state/storage.md` |

## Read Order for AI

```
AUTHORITY.md → platform/current_state.md → topic file → code
```

Never infer current API from ADR chain — **L1 only**.
