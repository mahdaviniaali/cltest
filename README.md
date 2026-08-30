# Crawler Project

پروژه کرالر وب با Python و Frontend — **documentation-first**.

## ساختار

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
