# Getting Started

```yaml
---
domain: shared
authority: L2
owner: onboarding
not_authoritative_for:
  - runtime config values (→ platform/current_state/config.md)
---
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (frontend — هنوز scaffold)

## Backend (Crawler)

```bash
cd project
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env    # Windows
# cp .env.example .env      # Linux/macOS
python scripts/init_db.py
python run_api.py
```

اسکریپت‌های operator: [`development/scripts.md`](scripts.md).

خروجی JSON در `project/data/` ذخیره می‌شود.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

> Frontend هنوز scaffold است — [`application/current_state/frontend.md`](../application/current_state/frontend.md).

## Read Next

1. [`AUTHORITY.md`](../AUTHORITY.md) — owner table
2. [`platform/current_state.md`](../platform/current_state.md) — facts کرالر
3. [`application/current_state.md`](../application/current_state.md) — facts محصول

## Env Vars

مقادیر canonical در [`platform/current_state/config.md`](../platform/current_state/config.md).
