# Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+ (برای frontend)

## Backend Setup

```bash
cd project
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Configuration

متغیرهای محیطی در `project/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `CRAWLER_DELAY` | `1.0` | تأخیر بین درخواست‌ها (ثانیه) |
| `CRAWLER_TIMEOUT` | `30` | timeout درخواست HTTP |
| `CRAWLER_USER_AGENT` | — | User-Agent سفارشی |
| `CRAWLER_OUTPUT_DIR` | `data/` | مسیر ذخیره خروجی |

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend روی `http://localhost:3000` اجرا می‌شود.
