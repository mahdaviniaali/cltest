# Schema — users & searches

```yaml
---
domain: application
authority: L5
maturity: working
owner: schema-users-searches
intent: explain
source: UC-U1..U7 + ADR 005/006
---
```

## users

| Column | Type | Note |
|---|---|---|
| `id` | INTEGER PK | internal |
| `email` | VARCHAR(255) UNIQUE | login identifier |
| `password_hash` | VARCHAR(255) | bcrypt |
| `full_name` | VARCHAR(128) | optional |
| `created_at` | TIMESTAMPTZ | |

## searches

| Column | Type | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | FK → users.id CASCADE | owner |
| `name` | VARCHAR(128) | optional label |
| `brand`, `model` | VARCHAR(128) | matching criteria |
| `min_year` | INTEGER | Persian year |
| `max_price` | BIGINT | tomans |
| `max_mileage` | INTEGER | km |
| `location` | VARCHAR(256) | |
| `enabled` | BOOLEAN | default true |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

## Auth (ADR 006)

- Register / login → JWT bearer token
- Password: bcrypt
- Protected routes: `/api/searches/*`, `/api/auth/me`

## API Endpoints

| Method | Path | UC |
|---|---|---|
| POST | `/api/auth/register` | UC-U1 |
| POST | `/api/auth/login` | UC-U1 |
| GET | `/api/auth/me` | UC-U1 |
| GET | `/api/searches` | UC-U3 |
| POST | `/api/searches` | UC-U2 |
| GET | `/api/searches/{id}` | UC-U3 |
| PUT | `/api/searches/{id}` | UC-U4 |
| DELETE | `/api/searches/{id}` | UC-U5 |
| PATCH | `/api/searches/{id}/toggle` | UC-U6 |

Multiple searches per user (UC-U7) via `user_id` FK — no extra constraint.
