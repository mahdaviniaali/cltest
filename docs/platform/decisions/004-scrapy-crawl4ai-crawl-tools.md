# ADR 004 — Scrapy & Crawl4AI as Crawl Infrastructure Tools

- Status: Accepted
- Date: 2026-08-30
- Supersedes: بخش «Rejected: Scrapy framework» در [ADR 001](001-layered-crawler-architecture.md)

## Context

پروژه Bama.ir نیاز به crawl دوره‌ای، استخراج structured data، retry/resilience، و احتمالاً render صفحات JS-heavy دارد.

معماری پروژه **Hexagonal (Ports & Adapters)** است — ابزار crawl نباید به domain/core گره بخورند.

## Decision

**Scrapy** و **Crawl4AI** به‌عنوان **infrastructure adapters** (ابزار) در لایه platform نصب و استفاده می‌شوند — **نه** به‌عنوان هسته معماری.

| ابزار | نقش adapter | قابلیت‌های مورد استفاده |
|---|---|---|
| **Scrapy** | crawl engine / spider orchestration | spider pipeline، scheduling hooks، middleware، retry، concurrent requests، item pipeline |
| **Crawl4AI** | browser-aware fetch + extraction | headless render، LLM-ready extraction، async crawl، markdown/structured output |

### قانون Hexagonal

```text
┌─────────────────────────────────────────┐
│  Domain / Application (ports)           │
│  CrawlPort · ExtractPort · AdRepository │
└──────────────────┬──────────────────────┘
                   │ implements
        ┌──────────┼──────────┐
        v          v          v
   ScrapyAdapter  Crawl4AIAdapter  HttpClientAdapter (existing)
        │          │          │
        └──────────┴──────────┘
              Infrastructure
```

- **Port:** قرارداد abstract (مثلاً `fetch_pages()`, `extract_ad()`) — domain فقط port را می‌شناسد.
- **Adapter:** پیاده‌سازی concrete با Scrapy / Crawl4AI / requests+BS4.
- **Swap:** تعویض adapter بدون تغییر domain logic.
- **No coupling:** import مستقیم Scrapy/Crawl4AI در application/domain **ممنوع** — فقط از composition root.

### هم‌زیستی با stack فعلی

`requests` + `BeautifulSoup` + `BaseCrawler` scaffold فعلی **باقی می‌ماند** — adapter سبک برای crawl ساده. Scrapy/Crawl4AI برای capabilityهای پیشرفته‌تر (concurrency، JS render) اضافه می‌شوند.

## Consequences

| ✅ | ❌ |
|---|---|
| ابزار production-grade برای Bama crawl | dependency footprint بزرگ‌تر (به‌ویژه Crawl4AI) |
| JS-rendered pages قابل handle | نیاز به adapter layer قبل از استفاده در domain |
| hexagonal boundary حفظ می‌شود | learning curve Scrapy spider model |
| چند adapter قابل A/B | ADR 001 «reject Scrapy» دیگر valid نیست |

## Rejected Alternatives

- **Scrapy as architecture core** — domain را به framework lock می‌کند؛ خلاف hexagonal
- **فقط requests+BS4** — برای Bama ممکن است JS-render یا scale کافی نباشد
- **Crawl4AI-only** — orchestration/scheduling/pipeline Scrapy م complement است نه جایگزین کامل

## Related

- [`platform/architecture/overview.md`](../architecture/overview.md) — hexagonal boundary
- [`platform/current_state/dependencies.md`](../current_state/dependencies.md) — package list
- [`001-layered-crawler-architecture.md`](001-layered-crawler-architecture.md) — layered structure (همچنان valid)
