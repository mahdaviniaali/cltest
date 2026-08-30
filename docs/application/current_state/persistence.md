# Application Persistence

```yaml
---
domain: application
authority: L1
owner: persistence
verify: project/src/app/models/advertisement.py
questions:
  - How are advertisements stored?
  - What is the dedup key?
not_authoritative_for:
  - why relational DB (→ platform/decisions/005)
  - draft schema rationale (→ spec/schema/advertisements.md)
---
```

## Database

| Property | Value |
|---|---|
| ORM | SQLAlchemy 2.x |
| Dev default | SQLite `data/app.db` |
| Config | `settings.DATABASE_URL` |
| Init script | `python scripts/init_db.py` |

## Table: `advertisements`

| Column | Type | Required | Note |
|---|---|---|---|
| `id` | BIGINT PK | yes | internal |
| `bama_id` | VARCHAR(32) | yes | **UNIQUE** — dedup key |
| `url` | VARCHAR(512) | yes | |
| `title` | VARCHAR(512) | yes | |
| `brand`, `model` | VARCHAR(128) | no | matching |
| `year` | INTEGER | no | |
| `price` | BIGINT | no | tomans |
| `mileage` | INTEGER | no | km |
| `location` | VARCHAR(256) | no | |
| `engine_capacity_cc` | INTEGER | no | |
| `transmission`, `fuel_type`, `body_type` | VARCHAR | no | |
| `body_color`, `interior_color`, `body_condition` | VARCHAR | no | |
| `seller_name`, `seller_phone`, `seller_address` | VARCHAR | no | |
| `description` | TEXT | no | |
| `technical_specs` | JSON | no | |
| `published_at` | TIMESTAMPTZ | no | |
| `crawled_at` | TIMESTAMPTZ | yes | default now |
| `raw_data` | JSON | no | |
| `is_deleted`, `is_sold` | BOOLEAN | yes | default false |

## Repository

| Class | Module |
|---|---|
| `AdvertisementRepository` | `app.repositories.advertisement_repository` |

| Method | Behavior |
|---|---|
| `get_by_bama_id(bama_id)` | fetch by dedup key |
| `exists(bama_id)` | bool |
| `save_new(data)` | insert if new → `(Ad, created)` |
| `update_status(bama_id, …)` | patch `is_deleted` / `is_sold` |
| `list_active(limit)` | not deleted/sold, newest first |

## Env

| Variable | Default |
|---|---|
| `DATABASE_URL` | `sqlite:///data/app.db` |
