# Bama.ir Crawler & Notification System

> **Bama.ir New Ads Crawler & Notification System** — مانیتور آگهی‌های جدید خودرو، تطبیق با فیلتر کاربر، و ارسال اعلان.

---

## روایت پیشرفت پروژه

این بخش **گزارش مسیر کار** است — نه فقط «چی ساخته شده»، بلکه **چرا و چطور** به هر تصمیم رسیده‌ام.  
هدف: شفاف بودن فرآیند فکری برای reviewer و تیم، قبل از اینکه کد نهایی merge شود.

### مدل کاری من

```text
خواندن → درک → بحث → ثبت → تصمیم → پیاده‌سازی
```

قبل از نوشتن کد، ترجیح می‌دهم **مسئله را درست تعریف کنم**.  
هر ایده‌ای که در حین خواندن پروژه به ذهنم می‌رسد، یادداشت می‌شود؛ روی trade-offها بحث می‌کنم؛ و فقط وقتی scope و رویکرد برای یک بخش روشن شد، می‌روم سراغ implementation.

این README به‌مرور با هر مرحله‌ای که طی می‌کنم به‌روز می‌شود.

---

### مرحله ۱ — تعریف و درک پروژه

**وضعیت:** ✅ انجام شده

اولین اولویتم این بود که **دقیقاً بدانم چه چیزی باید ساخته شود** — نه اینکه زود وارد stack یا framework شوم.

تسک را خط‌به‌خط خواندم و مشخص کردم سیستم در نهایت چه جریانی دارد:  
Bama.ir → crawl دوره‌ای → تشخیص آگهی جدید → ذخیره → match با فیلتر کاربر → notification.

**کارهایی که انجام دادم:**

- متن تسک را به یک **تعریف رسمی پروژه** تبدیل کردم — scope، subsystemها، entityها، و مرز in/out.
- مشخص کردم scaffold فعلی (کرالر پایه + JSON storage) **کجای مسیر** قرار دارد و **gap** کجاست.
- تصمیم گرفتم موارد باز (DB، queue، auth، channel اعلان) را عمداً lock نکنم و به فاز رویکرد بسپارم.

**خروجی:**

| سند | محتوا |
|---|---|
| [`docs/base/تعریف_پروژه.md`](docs/base/تعریف_پروژه.md) | تعریف محصول، requirements، subsystemها |

**یادداشت:** در این مرحله هنوز کد production ننوشتم — عمداً. هدف «فهمیدن قبل از ساختن» بود.

---

### مرحله ۲ — استخراج Use Caseها

**وضعیت:** ✅ انجام شده

بعد از تعریف پروژه، requirements را به **use caseهای قابل‌لمس** تبدیل کردم.  
دلیلش ساده است: وقتی سناریوها جلوی چشم باشند، راحت‌تر می‌شود فهمید هر subsystem دقیقاً چه کاری انجام می‌دهد و چه چیزی out of scope است.

**کارهایی که انجام دادم:**

- use caseها را در پنج دسته گروه‌بندی کردم: Crawling · User & Filters · Matching · Notifications · NFR
- یک **سناریوی End-to-End** نوشتم — از ثبت فیلتر توسط کاربر تا دریافت اعلان تلگرام/ایمیل
- موارد ambiguous (مثل auth model یا انتخاب channel توسط کاربر) را با برچسب *(TBD)* علامت زدم تا در فاز رویکرد بسته شوند

**خروجی:**

| سند | محتوا |
|---|---|
| [`docs/base/تعریف_پروژه.md#use-cases`](docs/base/تعریف_پروژه.md) | جدول UCها + سناریوی E2E |

**یادداشت:** این use caseها پایه تست acceptance و بحث‌های architecture session بعدی خواهند بود.

---

### مرحله ۳ — چارچوب رویکرد (در جریان)

**وضعیت:** 🔄 در حال انجام

الان در مرحله‌ای هستم که **پروژه را آرام می‌خوانم** و برای هر بخش ایده و نظر ثبت می‌کنم.  
قبل از implementation، برای هر مشکل یک رویکرد مشخص می‌دهیم — stack، معماری، و ترتیب delivery.

**کارهایی که تا اینجا انجام شده:**

- سیستم مستندسازی لایه‌ای (L1–L5) و methodology پروژه را بررسی کردم
- رویکرد **documentation-first** و **architecture before code** را با ساختار repo هم‌راستا دیدم
- open questions اولیه را شناسایی کردم (DB، async model، notification channel، K8s topology، …)

**خروجی‌های مرتبط:**

| سند | محتوا |
|---|---|
| [`docs/base/رویکرد_پروژه.md`](docs/base/رویکرد_پروژه.md) | فازها، gateها، decision framework |
| [`docs/application/spec/open_questions.md`](docs/application/spec/open_questions.md) | سؤالات باز با owner |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | فلسفه مستندسازی |

**قدم بعدی:** schema جداول باقی‌مانده (users, searches, matches, notifications) + open questions Phase 1.

**تصمیم اخیر — schema آگهی‌ها:**

- فیلدهای Bama.ir inspect شد → جدول `advertisements` با ۲۷ ستون طراحی شد
- dedup key: `bama_id` (UNIQUE)
- Spec: [`docs/application/spec/schema/advertisements.md`](docs/application/spec/schema/advertisements.md)
- OQ-008 بسته شد

**تصمیم اخیر — persistence / schema:**

- با توجه به سایت مشخص (Bama.ir) و وقت محدود، **schema را دستی** طراحی می‌کنم — نه entity detection با XPath/CSS
- **Relational DB:** SQLite برای dev/MVP، PostgreSQL برای production
- ADR: [`docs/platform/decisions/005-relational-db-manual-schema.md`](docs/platform/decisions/005-relational-db-manual-schema.md)
- OQ-007 بسته شد

**تصمیم اخیر — ابزار crawl:**

- **Scrapy** و **Crawl4AI** نصب شدند (`project/requirements.txt`)
- معماری **Hexagonal** — این‌ها فقط **infrastructure adapter** هستند، نه هسته domain
- ADR: [`docs/platform/decisions/004-scrapy-crawl4ai-crawl-tools.md`](docs/platform/decisions/004-scrapy-crawl4ai-crawl-tools.md)
- جزئیات ports/adapters: [`docs/platform/architecture/hexagonal_crawl_tools.md`](docs/platform/architecture/hexagonal_crawl_tools.md)

---

### مرحله ۴ — پیاده‌سازی

**وضعیت:** ⏳ منتظر gate مرحله ۳

Implementation بعد از بسته شدن رویکرد Phase 1 شروع می‌شود — نه preemptive.

**ترتیب پیش‌بینی‌شده:**

```text
Phase 1 → Bama crawler + dedup + persistence
Phase 2 → API + matching + notification
Phase 3 → K8s + observability + polish
```

---

## ساختار repo

```
cltest/
├── docs/          # سیستم دانش لایه‌ای (L1–L5)
├── project/       # کرالر Python (platform + application code)
└── frontend/      # رابط کاربری (scaffold)
```

## شروع سریع

```bash
# Backend
cd project
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python main.py
```

## مستندات

**Entry point:** [`docs/README.md`](docs/README.md)

| سند | نقش |
|---|---|
| [`docs/base/تعریف_پروژه.md`](docs/base/تعریف_پروژه.md) | تعریف، requirements، use cases |
| [`docs/base/رویکرد_پروژه.md`](docs/base/رویکرد_پروژه.md) | رویکرد معماری و فازها |
| [`docs/AUTHORITY.md`](docs/AUTHORITY.md) | مدل authority + owner table |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | فلسفه مستندسازی |
| [`docs/development/getting_started.md`](docs/development/getting_started.md) | onboarding |
| [`docs/development/development_rules.md`](docs/development/development_rules.md) | قوانین engineering |
| [`docs/development/documentation_rules.md`](docs/development/documentation_rules.md) | قوانین مستندنویسی |

## Domains

| Domain | Docs | Code |
|---|---|---|
| Platform | [`docs/platform/`](docs/platform/) | `project/src/crawler/` |
| Application | [`docs/application/`](docs/application/) | `project/main.py`, `frontend/` |

---

*آخرین به‌روزرسانی روایت: مرحله ۳ — تصمیم DB/schema (ADR 005) — مرداد ۱۴۰۵*
