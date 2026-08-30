# Schema — advertisements

```yaml
---
domain: application
authority: L5
maturity: working
owner: schema-advertisements
intent: explain
source: Bama.ir ad page inspection + ADR 005
questions:
  - جدول آگهی‌ها چه فیلدهایی دارد؟
  - dedup key چیست؟
not_authoritative_for:
  - shipped DDL (→ current_state/ after code)
  - users / searches / matches (→ sibling schema docs)
---
```

**Document intent:** Draft schema جدول `advertisements` — بر اساس فیلدهای واقعی Bama.ir.  
**ADR:** [005-relational-db-manual-schema](../../platform/decisions/005-relational-db-manual-schema.md)

## Dedup Key

| کلید | ستون | قانون |
|---|---|---|
| **Primary dedup** | `bama_id` | `UNIQUE NOT NULL` — شماره آگهی در Bama |
| Fallback | `url` | اگر `bama_id` نامعتبر بود → از URL استخراج یا `UNIQUE(url)` |

→ **OQ-008 closed:** Bama stable ad ID موجود است (`bama_id`).

---

## Field Map (فارسی → SQL)

| فیلد (فارسی) | Column | Type | Null | مثال / note |
|---|---|---|---|---|
| شناسه داخلی | `id` | `BIGSERIAL` / `INTEGER PK` | NO | auto — ما تولید می‌کنیم |
| شناسه باما | `bama_id` | `VARCHAR(32)` | NO | `1234567` — **UNIQUE** |
| لینک | `url` | `VARCHAR(512)` | NO | `https://bama.ir/car/1234567` |
| عنوان | `title` | `VARCHAR(512)` | NO | رنو مگان ۲۰۰۰ ۱۳۸۹ |
| برند | `brand` | `VARCHAR(128)` | YES | رنو |
| مدل | `model` | `VARCHAR(128)` | YES | مگان |
| سال | `year` | `SMALLINT` | YES | `1389` — سال شمسی |
| قیمت (تومان) | `price` | `BIGINT` | YES | `2200000000` |
| کارکرد (km) | `mileage` | `INTEGER` | YES | `249000` |
| موقعیت | `location` | `VARCHAR(256)` | YES | بابلسر، مازندران |
| حجم موتور (cc) | `engine_capacity_cc` | `SMALLINT` | YES | `2000` |
| گیربکس | `transmission` | `VARCHAR(32)` | YES | `automatic` / `manual` |
| سوخت | `fuel_type` | `VARCHAR(32)` | YES | `petrol` / `diesel` |
| نوع بدنه | `body_type` | `VARCHAR(64)` | YES | sedan / hatchback / … |
| رنگ بدنه | `body_color` | `VARCHAR(64)` | YES | زیتونی |
| رنگ داخل | `interior_color` | `VARCHAR(64)` | YES | مشکی |
| وضعیت بدنه | `body_condition` | `VARCHAR(128)` | YES | خط و خش جزئی |
| نام فروشنده | `seller_name` | `VARCHAR(256)` | YES | شرکت دیزل ران |
| شماره فروشنده | `seller_phone` | `VARCHAR(32)` | YES | `091221212XX` |
| آدرس فروشنده | `seller_address` | `VARCHAR(512)` | YES | اسلامشهر، بلوار پیامبر |
| توضیحات | `description` | `TEXT` | YES | متن آگهی |
| مشخصات فنی | `technical_specs` | `JSONB` / `JSON` | YES | `{power, torque, acceleration, …}` |
| زمان انتشار | `published_at` | `TIMESTAMPTZ` | YES | زمان publish در Bama |
| زمان خزش | `crawled_at` | `TIMESTAMPTZ` | NO | default `NOW()` |
| داده خام | `raw_data` | `JSONB` / `JSON` | YES | کل payload استخراج‌شده |
| حذف شده؟ | `is_deleted` | `BOOLEAN` | NO | default `FALSE` |
| فروخته شده؟ | `is_sold` | `BOOLEAN` | NO | default `FALSE` |

---

## DDL (PostgreSQL)

```sql
CREATE TABLE advertisements (
    id                  BIGSERIAL PRIMARY KEY,
    bama_id             VARCHAR(32)  NOT NULL,
    url                 VARCHAR(512) NOT NULL,
    title               VARCHAR(512) NOT NULL,

    brand               VARCHAR(128),
    model               VARCHAR(128),
    year                SMALLINT,
    price               BIGINT,
    mileage             INTEGER,
    location            VARCHAR(256),

    engine_capacity_cc  SMALLINT,
    transmission        VARCHAR(32),
    fuel_type           VARCHAR(32),
    body_type           VARCHAR(64),
    body_color          VARCHAR(64),
    interior_color      VARCHAR(64),
    body_condition      VARCHAR(128),

    seller_name         VARCHAR(256),
    seller_phone        VARCHAR(32),
    seller_address      VARCHAR(512),
    description         TEXT,

    technical_specs     JSONB,
    published_at        TIMESTAMPTZ,
    crawled_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data            JSONB,

    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    is_sold             BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT uq_advertisements_bama_id UNIQUE (bama_id)
);

-- matching / filter queries
CREATE INDEX idx_advertisements_brand_model ON advertisements (brand, model);
CREATE INDEX idx_advertisements_year ON advertisements (year);
CREATE INDEX idx_advertisements_price ON advertisements (price);
CREATE INDEX idx_advertisements_mileage ON advertisements (mileage);
CREATE INDEX idx_advertisements_location ON advertisements (location);
CREATE INDEX idx_advertisements_published_at ON advertisements (published_at DESC);
CREATE INDEX idx_advertisements_crawled_at ON advertisements (crawled_at DESC);
CREATE INDEX idx_advertisements_active ON advertisements (is_deleted, is_sold)
    WHERE is_deleted = FALSE AND is_sold = FALSE;
```

---

## DDL (SQLite — dev/MVP)

```sql
CREATE TABLE advertisements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bama_id             TEXT NOT NULL UNIQUE,
    url                 TEXT NOT NULL,
    title               TEXT NOT NULL,

    brand               TEXT,
    model               TEXT,
    year                INTEGER,
    price               INTEGER,
    mileage             INTEGER,
    location            TEXT,

    engine_capacity_cc  INTEGER,
    transmission        TEXT,
    fuel_type           TEXT,
    body_type           TEXT,
    body_color          TEXT,
    interior_color      TEXT,
    body_condition      TEXT,

    seller_name         TEXT,
    seller_phone        TEXT,
    seller_address      TEXT,
    description         TEXT,

    technical_specs     TEXT,   -- JSON string
    published_at        TEXT,   -- ISO-8601
    crawled_at          TEXT NOT NULL DEFAULT (datetime('now')),
    raw_data            TEXT,   -- JSON string

    is_deleted          INTEGER NOT NULL DEFAULT 0,
    is_sold             INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_advertisements_brand_model ON advertisements (brand, model);
CREATE INDEX idx_advertisements_year ON advertisements (year);
CREATE INDEX idx_advertisements_price ON advertisements (price);
CREATE INDEX idx_advertisements_mileage ON advertisements (mileage);
CREATE INDEX idx_advertisements_published_at ON advertisements (published_at);
```

---

## Matching-Relevant Columns

فیلتر کاربر (search criteria) معمولاً روی این ستون‌ها match می‌شود:

| criteria | column |
|---|---|
| Brand | `brand` |
| Model | `model` |
| Min/Max Year | `year` |
| Max Price | `price` |
| Max Mileage | `mileage` |
| Location | `location` |

سایر فیلدها (رنگ، گیربکس، …) optional filter در فاز بعد — MVP روی ستون‌های بالا.

---

## Notes

- **`technical_specs`** و **`raw_data`**: JSON — parser می‌تواند فیلدهای nested (قدرت، گشتاور، شتاب) را بدون migration اضافه کند.
- **`is_deleted` / `is_sold`**: crawl بعدی وضعیت را update می‌کند — آگهی حذف/فروخته‌شده دوباره notify نمی‌شود.
- **`crawled_at`**: first-seen timestamp؛ برای re-crawl می‌توان `updated_at` بعداً اضافه کرد.
- **Normalization**: برند/مدل فعلاً `VARCHAR` — lookup table در فاز بعد در صورت نیاز.

## Related

| سند | محتوا |
|---|---|
| [`تعریف_پروژه.md`](../../base/تعریف_پروژه.md) | minimum fields + use cases |
| [`005-relational-db-manual-schema.md`](../../platform/decisions/005-relational-db-manual-schema.md) | چرا relational + manual schema |
