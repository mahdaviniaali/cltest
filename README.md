# Bama.ir Crawler & Notification System

> مانیتور آگهی‌های جدید خودرو در Bama.ir → dedup → match با فیلتر کاربر → notify

سیستم production-oriented برای تسک فنی Bama.ir: crawl اخلاقی، persistence رابطه‌ای، API کاربر، matching idempotent، notification چندکاناله، async با Celery، و deploy با Docker/K8s.

---

## معماری در یک نگاه

```text
┌──────────────┐     REST/JWT      ┌─────────────────────────────────────────┐
│   Frontend   │ ───────────────► │  FastAPI (searches · ads · notify · API) │
└──────────────┘                  └───────────────┬─────────────────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
           ┌────────────────┐           ┌─────────────────┐           ┌─────────────────┐
           │ MatchingEngine │           │ FilterCrawlSvc  │           │ Notification    │
           │ (SQL prefilter)│           │ (fingerprint)   │           │ Orchestrator    │
           └───────┬────────┘           └────────┬────────┘           └────────┬────────┘
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 │
                                                 ▼
                              ┌──────────────────────────────────┐
                              │  PostgreSQL / SQLite             │
                              │  ads · searches · matches ·      │
                              │  outbox · crawl_jobs · taxonomy  │
                              └──────────────────┬───────────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    ▼                            ▼                            ▼
           ┌────────────────┐          ┌─────────────────┐          ┌─────────────────┐
           │ Celery workers │          │ Crawler (ports) │          │ Redis (broker)  │
           │ crawl·match·   │          │ incremental ·   │          │                 │
           │ notify·outbox  │          │ filter · sitemap│          │                 │
           └────────────────┘          └────────┬────────┘          └─────────────────┘
                                                │
                                                ▼
                                         Bama.ir (HTTP)
                                         robots + rate limit
```

**اصل طراحی:** Platform/Application split — کرالر پشت port (hexagonal)، domain به Scrapy/Crawl4AI/requests وابسته نیست.

---

## Use Case → راه‌حل

هر UC از [`docs/base/تعریف_پروژه.md`](docs/base/تعریف_پروژه.md) به یک تصمیم معماری و کد مشخص map شده است.

### Crawling

| UC | نیاز | راه‌حل | کد / ADR |
|---|---|---|---|
| **UC-C1** | crawl دوره‌ای آگهی جدید | Celery Beat هر `CRAWL_INTERVAL_SECONDS` → `crawl.scheduled_tick` (filterها اول، بعد global incremental) | ADR-006 · `app/workers/tasks/crawl.py` |
| **UC-C2** | extract فیلدهای آگهی | `BamaListingParser` + `BamaDetailParser` روی HTML — pure function، بدون side effect | `crawler/adapters/bama/parsers.py` |
| **UC-C3** | تشخیص آگهی جدید | checkpoint `crawler_state.last_seen_bama_id` — لیستینگ newest-first تا برخورد با checkpoint | `incremental_crawl.py` |
| **UC-C4** | ذخیره normalize‌شده | `DbAdStore.save_new()` — `UNIQUE(bama_id)` + outbox در همان TX | `db_ad_store.py` · ADR-007 |
| **UC-C5** | resilience | `HttpClient` با retry/backoff روی 429/5xx؛ job status در `crawl_jobs`؛ stale job recovery | `http_client.py` · `cleanup_stale_jobs.py` |
| **UC-C6** | ethical crawl | `HttpPageFetcher(respect_robots=True)` + `CRAWL_DELAY_SECONDS` — بدون anti-bot bypass | ADR-006 · `http_page_fetcher.py` |
| **UC-C7** | interval قابل تنظیم | env: `CRAWL_INTERVAL_SECONDS`, `CRAWL_MAX_PAGES`, `CRAWL_STALENESS_SECONDS` | `config/settings.py` |

**ایده کلیدی crawl:** hybrid incremental — نه full re-crawl. scheduled برای cache مشترک + on-demand وقتی فیلتر کاربر stale است.

### User & Filters

| UC | نیاز | راه‌حل | کد / ADR |
|---|---|---|---|
| **UC-U1** | شناسایی کاربر | JWT auth — register/login/me | `app/api/routes/auth.py` · ADR-001 |
| **UC-U2** | ایجاد فیلتر | `POST /api/searches` — criteria → `filter_fingerprint` → crawl یا cache hit | `FilterCrawlService` · ADR-011 |
| **UC-U3** | لیست فیلترها | `GET /api/searches` scoped به `user_id` | `search_repository.py` |
| **UC-U4** | ویرایش | `PUT /api/searches/{id}` — fingerprint عوض شد → re-crawl + rematch | `searches.py` |
| **UC-U5** | حذف | `DELETE /api/searches/{id}` | `searches.py` |
| **UC-U6** | enable/disable | `enabled` flag — matching فقط روی searches فعال | `matching.py` |
| **UC-U7** | چند فیلتر | چند `Search` per user؛ dedup crawl با `filter_fingerprint` مشترک | `filter_job_dedup` tests |

**ایده کلیدی UX:** cache-first — preview از cache؛ crawl فقط بعد از save یا وقتی cache کافی نیست. پاسخ API همیشه `cached_count` + `is_crawling` برمی‌گرداند.

### Matching

| UC | نیاز | راه‌حل | کد |
|---|---|---|---|
| **UC-M1** | match روی ad جدید | outbox `ad.created` → Celery `match.process_ad` | `outbox_relay.py` |
| **UC-M2** | condition checking | `ad_matches_search_criteria()` — brand/model/year/price/mileage/location | `search_filter.py` |
| **UC-M3** | ثبت match | `UNIQUE(ad_id, search_id)` + SQL prefilter قبل از evaluate | `matching.py` |

### Notifications

| UC | نیاز | راه‌حل | کد / ADR |
|---|---|---|---|
| **UC-N1** | ارسال اعلان | `NotificationOrchestrator` → channel adapters (`in_app`, `log`, stub email/telegram) | ADR-010 |
| **UC-N2** | بدون notify تکراری | `UNIQUE(match_id, channel)` + `UNIQUE(ad_id, search_id)` | schema matches/notifications |
| **UC-N3** | channel قابل توسعه | `ChannelRegistry` + `NotificationChannel` port — کانال جدید بدون تغییر crawler/match | ADR-010 |

### Non-Functional

| UC | نیاز | راه‌حل |
|---|---|---|
| **UC-NF1** | مقیاس‌پذیری | Celery queueهای جدا (`filter`, `crawl`, `match`, `notify`)؛ fingerprint dedup برای جلوگیری از crawl تکراری |
| **UC-NF2** | observability | `/api/health/live` · `/api/health/ready` (DB+Redis) · `/api/metrics` (Prometheus) · structured logging |
| **UC-NF3** | K8s | `docker-compose.yml` + `k8s/cltest.yaml` — api, worker, beat, postgres, redis |
| **UC-NF4** | async | Transactional outbox + Celery — at-least-once، handlerها idempotent | ADR-007 |
| **UC-NF5** | REST API | FastAPI — 40+ endpoint (searches, ads, crawl, notify, inspector, taxonomy) | [`api.md`](docs/application/current_state/api.md) |

---

## تصمیم‌های معماری (خلاصه)

| ADR | تصمیم | چرا |
|---|---|---|
| [001](docs/platform/decisions/001-layered-crawler-architecture.md) | Layered crawler | جداسازی domain / application / adapters |
| [004](docs/platform/decisions/004-scrapy-crawl4ai-crawl-tools.md) | Scrapy/Crawl4AI پشت adapter | swap engine بدون تغییر use case |
| [005](docs/platform/decisions/005-relational-db-manual-schema.md) | PostgreSQL + schema دستی | SQLite dev، Postgres prod |
| [006](docs/platform/decisions/006-hybrid-incremental-crawl.md) | Hybrid incremental | فقط آگهی جدید، نه full crawl |
| [007](docs/platform/decisions/007-transactional-outbox-celery.md) | Outbox + Celery | ad → match → notify بدون از دست رفتن event |
| [008](docs/platform/decisions/008-site-map-inspector.md) | Site map Inspector | کشف ساختار سایت برای routing بهتر |
| [009](docs/platform/decisions/009-level-first-weighted-site-map.md) | Level-first BFS + weight | crawl هوشمندتر روی hubهای مهم |
| [010](docs/platform/decisions/010-extensible-notification-channels.md) | Channel registry | in_app الان؛ email/telegram بعداً |
| [011](docs/platform/decisions/011-task-job-filter-model.md) | Task/Job/Filter model | dedup crawl per fingerprint |

---

## Stack

| لایه | انتخاب |
|---|---|
| API | FastAPI + JWT + Pydantic v2 |
| ORM / DB | SQLAlchemy 2 · SQLite (dev) · PostgreSQL (prod) |
| Queue | Celery 5 + Redis |
| Crawl | requests + BS4/lxml · ports برای Scrapy/Crawl4AI |
| Frontend | React + Vite (dashboard + inspector) |
| Deploy | Docker Compose · Kubernetes manifests |
| Test | pytest (90+) · stress suite · Locust load tests |

---

## شروع سریع

### Docker (توصیه‌شده)

```bash
docker compose up --build
# API → http://localhost:8000
# Frontend → npm run dev در frontend/
```

### Local

```bash
cd project
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
python scripts/init_db.py

# ترمینال ۱ — API
python run_api.py

# ترمینال ۲ — worker + beat
celery -A app.workers.celery_app worker -Q filter,crawl,outbox_relay,match,notify -l info
celery -A app.workers.celery_app beat -l info
```

---

## تست

```bash
cd project

pytest                              # unit/integration (سریع)
pytest -m stress                    # stress + SLO metrics
STRESS_REPORT_JSON=1 pytest -m stress   # گزارش JSON

# load test — API باید بالا باشد
locust -f tests/load/locustfile.py --headless -u 200 -r 40 -t 3m --host http://127.0.0.1:8000
```

Stress tests به Bama.ir درخواست نمی‌زنند — `FakeFetcher` + network killswitch. متریک‌ها: RPS، P50/P95/P99، error rate، CPU، memory، DB latency/query count، Redis hit rate.

جزئیات: [`docs/development/scripts.md`](docs/development/scripts.md)

---

## ساختار repo

```text
cltest/
├── docs/                 # L1–L5 — تعریف، ADR، current_state
├── project/
│   ├── src/
│   │   ├── crawler/      # platform — ports, incremental, site map
│   │   └── app/          # application — API, matching, notify, workers
│   ├── tests/            # pytest + stress/ + load/
│   ├── scripts/          # operator CLI
│   └── config/           # bama_site.yaml, settings
├── frontend/             # React UI
├── docker-compose.yml
└── k8s/
```

---

## E2E — یک خط

```text
User saves filter → fingerprint → cache hit یا enqueue crawl
→ new ad stored + outbox → match worker → notify (in_app)
→ user sees notification in inbox
```

---

## مستندات

| سند | محتوا |
|---|---|
| [`docs/base/تعریف_پروژه.md`](docs/base/تعریف_پروژه.md) | requirements + use cases (منبع UCها) |
| [`docs/application/current_state/api.md`](docs/application/current_state/api.md) | API canonical |
| [`docs/platform/current_state/crawler.md`](docs/platform/current_state/crawler.md) | crawl runtime |
| [`docs/development/getting_started.md`](docs/development/getting_started.md) | onboarding |
| [`docs/AUTHORITY.md`](docs/AUTHORITY.md) | ownership model |

---

*Technical README — use-case traceability + architecture decisions. Details in `docs/`.*
