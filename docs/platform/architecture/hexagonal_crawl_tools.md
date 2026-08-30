# Hexagonal Architecture — Crawl Tools

```yaml
---
domain: platform
authority: L2
owner: architecture
intent: explain
questions:
  - Scrapy و Crawl4AI کجا در معماری قرار می‌گیرند؟
  - domain به کدام ابزار وابسته است؟
not_authoritative_for:
  - package versions (→ current_state/dependencies.md)
  - why chosen (→ decisions/004-scrapy-crawl4ai-crawl-tools.md)
---
```

## Principle

معماری پروژه **Hexagonal (Ports & Adapters)** است.

Scrapy و Crawl4AI **فقط ابزار infrastructure** هستند — adapter — نه بخشی از domain model.

## Layer Map

```text
                    ┌──────────────────────────┐
                    │   Application Layer      │
                    │   (composition root)     │
                    │   main.py · schedulers   │
                    └────────────┬─────────────┘
                                 │ wires
                    ┌────────────▼─────────────┐
                    │   Domain / Use Cases     │
                    │   crawl · dedup · match  │
                    │   (depends on PORTS only)│
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │ PORTS (interfaces)                  │
              │ PageFetcher · AdExtractor · AdStore │
              └──────────────────┬──────────────────┘
                                 │ implements
     ┌───────────────────────────┼───────────────────────────┐
     v                           v                           v
┌─────────────┐          ┌──────────────┐          ┌─────────────────┐
│ HttpClient  │          │ Scrapy       │          │ Crawl4AI        │
│ + BS4       │          │ Adapter      │          │ Adapter         │
│ (existing)  │          │              │          │                 │
└─────────────┘          └──────────────┘          └─────────────────┘
     Infrastructure adapters — swappable, not authoritative
```

## Tool Capabilities (planned usage)

### Scrapy

| Capability | Use in Bama project |
|---|---|
| Spider / crawl orchestration | periodic listing crawl |
| Concurrent requests | throughput با rate limit |
| Middleware | User-Agent، retry، robots.txt |
| Item pipeline | normalize → persist adapter |
| Scheduler hooks | interval-based trigger integration |

### Crawl4AI

| Capability | Use in Bama project |
|---|---|
| Headless browser render | صفحات JS-heavy Bama |
| Async crawl | non-blocking fetch paths |
| Structured extraction | ad detail fields |
| Markdown / clean content | optional preprocessing |

## Rules

| Rule | Detail |
|---|---|
| **R1** | Domain/application **never** import `scrapy` or `crawl4ai` directly |
| **R2** | هر ابزار پشت یک **port interface** پیاده می‌شود |
| **R3** | Composition root adapter مناسب را inject می‌کند |
| **R4** | تعویض adapter = infrastructure change — domain test بدون تغییر |
| **R5** | Scaffold فعلی (`BaseCrawler`, `HttpClient`) یک adapter سبک است — حذف نمی‌شود |

## Current vs Planned

| Component | Status | Role |
|---|---|---|
| `HttpClient` + `HtmlParser` | ✅ shipped | lightweight fetch/parse adapter |
| `BaseCrawler` | ✅ shipped | simple orchestration template |
| Scrapy adapter | 📋 planned | production crawl engine |
| Crawl4AI adapter | 📋 planned | JS-render + rich extraction |

> Packages نصب شده‌اند — adapter implementation در Phase 1.

## Related

- [ADR 004 — Scrapy & Crawl4AI](../decisions/004-scrapy-crawl4ai-crawl-tools.md)
- [Architecture overview](overview.md)
- [Dependencies](../current_state/dependencies.md)
