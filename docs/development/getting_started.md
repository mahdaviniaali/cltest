# راه‌اندازی پروژه

```yaml
---
domain: shared
authority: L2
owner: onboarding
verify: docker-compose.yml, project/.env.example, project/run_api.py, project/Dockerfile, frontend/package.json, frontend/vite.config.ts, k8s/cltest.yaml
questions:
  - چطور stack را بالا بیاورم؟
  - حداقل چه سرویس‌هایی باید اجرا شوند؟
not_authoritative_for:
  - مقادیر runtime canonical (→ platform/current_state/config.md)
  - قرارداد API (→ application/current_state/api.md)
  - اسکریپت‌های اپراتور (→ development/scripts.md)
---
```

**Bama.ir New Ads Crawler & Notification System** — مانیتور آگهی جدید، dedup، match با فیلتر کاربر، notification.

دو مسیر اجرا وجود دارد: **Docker Compose** (توصیه‌شده) و **لوکال** (venv). Frontend در هیچ‌کدام داخل Compose نیست؛ جدا با npm بالا می‌آید.

## پیش‌نیازها

| ابزار | حداقل | کاربرد |
|---|---|---|
| Docker + Compose | — | مسیر کامل (API, worker, beat, Postgres, Redis) |
| Python | 3.10+ (image: 3.12) | مسیر لوکال |
| Node.js | 18+ | Frontend (Vite) |
| Redis | 7 | broker سلری + readiness |
| Git | — | کلون repo |

کار از ریشهٔ `cltest/` انجام می‌شود.

## سرویس‌ها

| سرویس | نقش | بدون آن |
|---|---|---|
| **API** (`:8000`) | FastAPI — auth، searches، ads، notify | UI و کلاینت کار نمی‌کنند |
| **Redis** (`:6379`) | Celery broker/backend | worker بالا نمی‌آید؛ `GET /api/health/ready` → 503 |
| **Worker** | صف‌های `filter`, `crawl`, `outbox_relay`, `match`, `notify` | فیلتر ذخیره می‌شود؛ crawl / match / notify اجرا نمی‌شود |
| **Beat** | تیک دوره‌ای `CRAWL_INTERVAL_SECONDS` | فقط crawl آن‌دیماند |
| **PostgreSQL** (`:5432`) | دیتابیس در Docker / prod | لوکال پیش‌فرض SQLite است |
| **Frontend** (`:5173`) | React dashboard + inspector | API را مستقیم مصرف کنید |

---

## مسیر ۱ — Docker Compose (توصیه‌شده)

از ریشهٔ `cltest/`:

```bash
docker compose up --build
```

سرویس‌ها: `api`, `worker`, `beat`, `postgres`, `redis`.

| آدرس | چیست |
|---|---|
| http://localhost:8000 | API |
| http://localhost:8000/docs | Swagger |
| http://localhost:8000/api/health/live | liveness |
| http://localhost:8000/api/health/ready | DB + Redis |

Frontend را جدا اجرا کنید (بخش پایین).

توقف:

```bash
docker compose down
```

حذف volume پستگرس (`pgdata`): `docker compose down -v`.

---

## مسیر ۲ — لوکال (venv)

مناسب توسعهٔ API. دیتابیس پیش‌فرض SQLite (`project/data/app.db`). Redis همچنان لازم است.

### ۱) Redis

از ریشهٔ `cltest/` یا از `project/` (Compose همان‌جا فقط Redis دارد):

```bash
docker compose up redis -d
```

### ۲) Backend

```bash
cd project
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/init_db.py
```

Linux / macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
```

`pip install` به‌خاطر Scrapy و Crawl4AI ممکن است طول بکشد.

`run_api.py` هنگام استارت `upgrade_schema()` را هم صدا می‌زند؛ `init_db.py` برای اولین بار یا دیتابیس خالی است.

### ۳) API

از `project/` با venv فعال:

```bash
python run_api.py
```

uvicorn روی `0.0.0.0:8000` با reload. مسیرهای `src/` و `project/` داخل اسکریپت به `sys.path` اضافه می‌شوند.

### ۴) Worker و Beat

Celery `config` و `app` را import می‌کند؛ `PYTHONPATH` باید `src` و ریشهٔ `project/` باشد.

Windows (PowerShell) — دو ترمینال جدا، از `project/`:

```powershell
$env:PYTHONPATH = "src;."
celery -A app.workers.celery_app worker -Q filter,crawl,outbox_relay,match,notify -l info
```

```powershell
$env:PYTHONPATH = "src;."
celery -A app.workers.celery_app beat -l info
```

Linux / macOS:

```bash
export PYTHONPATH=src:.
celery -A app.workers.celery_app worker -Q filter,crawl,outbox_relay,match,notify -l info
celery -A app.workers.celery_app beat -l info
```

بدون worker، ذخیرهٔ فیلتر API را می‌دهد ولی crawl و notification انجام نمی‌شود.

---

## Frontend

Compose فرانت را بالا نمی‌آورد. از ریشهٔ `cltest/`:

```bash
cd frontend
npm install
npm run dev
```

Vite روی **http://localhost:5173** — پروکسی `/api` → `http://localhost:8000`.

| مسیر UI | صفحه |
|---|---|
| `/register` | ثبت‌نام |
| `/login` | ورود |
| `/` | داشبورد فیلترها |
| `/searches/:id` | نتایج فیلتر |
| `/admin/inspector` | site map / درخت / رویدادها |

اولین استفاده: ثبت‌نام → ساخت فیلتر → در صورت stale بودن cache، worker باید بالا باشد تا crawl شروع شود.

---

## بررسی سلامت

```bash
curl http://localhost:8000/api/health/live
curl http://localhost:8000/api/health/ready
```

| پاسخ | معنی |
|---|---|
| live `{"status":"ok"}` | فرایند API زنده است |
| ready 200 | SQLite/Postgres و Redis در دسترس‌اند |
| ready 503 | یکی از `database` یا `redis` خراب است |

Swagger: http://localhost:8000/docs

اسکریپت وضعیت دیتا (از `project/`):

```bash
python scripts/inspect_data.py
```

اگر UI روی «در حال بروزرسانی» گیر کرد:

```bash
python scripts/cleanup_stale_jobs.py
```

جزئیات: [`scripts.md`](scripts.md).

---

## متغیرهای محیط

قالب committed: [`project/.env.example`](../../project/.env.example)  
فایل محلی: `project/.env` (gitignore).

| متغیر | پیش‌فرض قالب | نقش |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/app.db` | SQLite لوکال؛ در Compose پستگرس |
| `JWT_SECRET_KEY` | `change-me-in-production` | امضای JWT — در prod عوض شود |
| `CORS_ORIGINS` | `http://localhost:5173` | origin فرانت |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | در Compose: `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | همان broker | |
| `BAMA_LISTING_URL` | `https://bama.ir/car` | لیستینگ آگهی |
| `CRAWL_INTERVAL_SECONDS` | `300` | تیک Beat |
| `CRAWL_MAX_PAGES` | `10` | سقف صفحه در crawl دوره‌ای |
| `CRAWL_DELAY_SECONDS` | `1.0` | فاصلهٔ ethical بین درخواست‌ها |
| `CRAWL_STALENESS_SECONDS` | `600` (قالب) | تازگی cache فیلتر |
| `NOTIFICATION_CHANNELS_ENABLED` | `in_app,log` (Compose) | کانال‌های فعال |

کانال‌های email / telegram فقط اگر `SMTP_*` یا `TELEGRAM_BOT_TOKEN` ست شوند. مقادیر کامل کد: [`project/config/settings.py`](../../project/config/settings.py).

Compose این‌ها را override می‌کند: Postgres URL، Redis داخل شبکه، `JWT_SECRET_KEY=dev-docker-secret`.

---

## تست

از `project/` با venv فعال (`pytest.ini` مسیر `src .` را می‌گذارد):

```bash
pytest
pytest -m stress
STRESS_REPORT_JSON=1 pytest -m stress
```

`pytest` پیش‌فرض marker `stress` را رد می‌کند. Stress به Bama.ir درخواست نمی‌زند.

Load test — API باید بالا باشد:

```bash
locust -f tests/load/locustfile.py --headless -u 200 -r 40 -t 3m --host http://127.0.0.1:8000
```

جزئیات و SLO: [`scripts.md`](scripts.md).

---

## Kubernetes

مانیفست: [`k8s/cltest.yaml`](../../k8s/cltest.yaml) — Deploymentهای `cltest-api`, `cltest-worker`, `cltest-beat`, `cltest-redis`.

1. ایمیج را بسازید (همان Dockerfile بک‌اند):

```bash
docker build -t cltest-api:latest ./project
```

2. اعمال:

```bash
kubectl apply -f k8s/cltest.yaml
```

Secret داخل مانیفست `DATABASE_URL` را به هاست `cltest-postgres` می‌دهد. سرویس Postgres در همین فایل تعریف نشده؛ باید جدا در کلاستر باشد. `JWT_SECRET_KEY` را قبل از استفادهٔ واقعی عوض کنید.

---

## مشکلات رایج

| نشانه | کار |
|---|---|
| `GET /api/health/ready` → 503 و `redis` خطا | Redis را بالا بیاورید؛ URL را با `CELERY_BROKER_URL` چک کنید |
| فیلتر ذخیره شد ولی آگهی نمی‌آید | worker با صف‌های بالا باید در حال اجرا باشد |
| crawl دوره‌ای نیست | beat را جدا اجرا کنید |
| `ModuleNotFoundError: app` یا `config` در Celery | `PYTHONPATH=src;.` (ویندوز) / `src:.` (یونیکس) از داخل `project/` |
| CORS در مرورگر | `CORS_ORIGINS` شامل origin فرانت باشد؛ با Vite از پورت 5173 پروکسی `/api` کافی است |
| UI گیر روی در حال بروزرسانی | `python scripts/cleanup_stale_jobs.py` |
| پورت 8000/5173/6379/5432 اشغال | سرویس قبلی را ببندید یا پورت را عوض کنید |

---

## بعد از بالا آمدن

1. [`تعریف_پروژه.md`](../base/تعریف_پروژه.md) — scope و UCها
2. [`api.md`](../application/current_state/api.md) — endpointها
3. [`crawler.md`](../platform/current_state/crawler.md) — رفتار crawl
4. [`AUTHORITY.md`](../AUTHORITY.md) — owner اسناد
