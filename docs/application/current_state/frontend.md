# Application Frontend

```yaml
---
domain: application
authority: L1
owner: frontend
verify: frontend/
questions:
  - What framework and pages exist?
not_authoritative_for:
  - API contract details (→ persistence.md, spec/schema/)
---
```

## Stack

| Item | Value |
|---|---|
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| Routing | react-router-dom 6 |
| API proxy | `/api` → `http://localhost:8000` |

## Pages

| Route | Component | Purpose |
|---|---|---|
| `/login` | `LoginPage` | ورود |
| `/register` | `RegisterPage` | ثبت‌نام |
| `/` | `DashboardPage` | لیست و مدیریت فیلترها |
| `/searches/:id` | `SearchResultsPage` | نتایج فیلتر ذخیره‌شده |
| `/admin/inspector` | `InspectorPage` | Site map، درخت، گراف، رویدادهای زنده |

## User Features (implemented)

| UC | Feature |
|---|---|
| UC-U1 | Register, login, logout, JWT session |
| UC-U2 | Create search filter |
| UC-U3 | List filters |
| UC-U4 | Edit filter |
| UC-U5 | Delete filter |
| UC-U6 | Toggle enable/disable |
| UC-U7 | Multiple filters per user |

## Run

```bash
cd frontend
npm install
npm run dev
```

Requires API: `cd project && python run_api.py`

## Build output

`frontend/dist/`
