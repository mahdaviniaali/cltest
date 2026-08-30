# ADR 005 — Relational Database با Schema دستی

- Status: Accepted
- Date: 2026-08-30
- Closes: [OQ-007](../../application/spec/open_questions.md)
- Supersedes (production persistence): [ADR 002](002-json-storage.md) — JSON فقط scaffold Phase 0

## Context

تسک Bama.ir نیاز به persistence production-grade دارد:

- ذخیره آگهی‌ها با dedup
- CRUD فیلتر/جستجوی کاربر
- matching `(ad, search)`
- idempotency notification — `(ad + user + search)` حداکثر یک‌بار notify

Target site **مشخص** است (Bama.ir — آگهی خودرو) و فیلدهای Advertisement در [`تعریف_پروژه.md`](../../base/تعریف_پروژه.md) از قبل تعریف شده‌اند.

**محدودیت:** وقت محدود — schema نباید از کشف خودکار entity یا over-engineering schema شروع شود.

## Decision

### ۱. دیتابیس جدولی (Relational)

Persistence اصلی production روی **relational database**:

| محیط | انتخاب |
|---|---|
| Development / MVP | SQLite (یا PostgreSQL local) |
| Production | PostgreSQL |

Entityها رابطه‌محورند — `users`, `searches`, `advertisements`, `matches`, `notifications` — و constraint/index برای dedup و idempotency لازم است.

### ۲. Schema دستی — نه Entity Detection

Schema **دستی** و upfront طراحی می‌شود:

```text
تسک (فیلدهای اجباری Advertisement)
  + یک بررسی سریع HTML Bama.ir
  → جداول و ستون‌ها
  → parser همان فیلدها را populate می‌کند
```

**رد شده برای این پروژه:**

- کشف خودکار entity از DOM با XPath/CSS selector mining
- schema-less-first با normalize بعداً
- normalization سنگین (مثلاً lookup table برند/مدل) در MVP

دلیل: سایت ثابت + requirements از قبل known → کشف خودکار **هزینه بالا، ارزش پایین** در scope این تسک.

### ۳. Scope محدود Schema (time-box)

طراحی schema در **~۳۰–۴۵ دقیقه** time-box می‌شود:

| include (MVP) | defer |
|---|---|
| جداول core پنج‌گانه | JSONB پیچیده برای criteria |
| ستون‌های criteria اصلی فیلتر | lookup tables برند/مدل |
| `UNIQUE` روی dedup key آگهی | migration strategy پیشرفته |
| `UNIQUE(ad_id, search_id)` برای notify idempotency | audit tables اضافی |

Dedup key (`external_id` از Bama یا URL/hash) در schema تعریف می‌شود — جزئیات inspect Bama در implementation (مرتبط با OQ-008).

## Consequences

| ✅ | ❌ |
|---|---|
| query/match/filter طبیعی با SQL | نیاز به infra DB (Postgres) در production |
| dedup + idempotency با constraint | migration از JSON scaffold لازم است |
| مناسب تسک interview (persistence, API, production) | document DB flexibility از دست می‌رود — برای این scope قابل قبول |
| schema سریع از task spec — بدون وقت تلف روی discovery | schema اولیه ممکن است بعداً نیاز به migration داشته باشد |

## Rejected Alternatives

| گزینه | چرا رد شد |
|---|---|
| **MongoDB / document-first** | relations و unique constraints مهم‌تر از schema flexibility |
| **JSON file (ADR 002)** | dedup، multi-user، matching، notify idempotency — کافی نیست |
| **XPath/CSS entity auto-detection** | over-engineering برای سایت مشخص با spec از قبل |
| **PostgreSQL-only from day 1** | SQLite/local برای dev سریع‌تر — Postgres برای deploy |

## Related

- [`تعریف_پروژه.md`](../../base/تعریف_پروژه.md) — entityها و فیلدهای Advertisement
- [`002-json-storage.md`](002-json-storage.md) — superseded for production (scaffold only)
- [`open_questions.md`](../../application/spec/open_questions.md) — OQ-007, OQ-008 closed
- [`schema/advertisements.md`](../../application/spec/schema/advertisements.md) — DDL draft
