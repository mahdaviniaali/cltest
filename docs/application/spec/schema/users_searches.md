# Schema — users & searches

```yaml
---
domain: application
authority: L5
maturity: working
owner: schema-users-searches
intent: explain
source: UC-U1..U7 + ADR 005/006/011
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
| `section_key` | VARCHAR(64) | `car`, `motorcycle`, `truck` (default `car`) |
| `brand`, `model` | VARCHAR(128) | matching criteria (display labels) |
| `brand_term_id`, `model_term_id` | INTEGER FK → taxonomy_terms | optional crawl scope |
| `min_year` | INTEGER | Persian year |
| `max_price` | BIGINT | tomans |
| `max_mileage` | INTEGER | km |
| `location` | VARCHAR(256) | |
| `enabled` | BOOLEAN | default true |
| `filter_fingerprint` | VARCHAR(64) | SHA256 of canonical criteria — shared crawl unit (ADR-011) |
| `bootstrapped_at` | TIMESTAMPTZ | when filter cache first satisfied |
| `last_bootstrap_job_id` | VARCHAR(36) | last crawl job for this search |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

### Indexes (ADR-011)

| Index | Columns | Use |
|---|---|---|
| `ix_searches_fingerprint_enabled` | `filter_fingerprint`, `enabled` | users sharing exact filter |
| `ix_searches_brand_term_enabled` | `brand_term_id`, `enabled` | taxonomy brand lookup |
| `ix_searches_brand_enabled` | `brand`, `enabled` | label fallback (e.g. بنز) |

## Filter update flow (ADR-011)

When filter criteria change via `PUT /api/searches/{id}`:

1. Recompute `filter_fingerprint`
2. Reset `bootstrapped_at` / `last_bootstrap_job_id`
3. Enqueue `ON_DEMAND_FILTER` if new fingerprint cache is stale
4. Rematch existing ads when cache is already sufficient

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
