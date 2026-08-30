# Application Persistence

```yaml
---
domain: application
authority: L1
owner: persistence
verify: project/src/app/models/
questions:
  - How are advertisements, users, and searches stored?
  - What is the dedup key for ads?
not_authoritative_for:
  - why relational DB (→ platform/decisions/005)
  - draft schema rationale (→ spec/schema/)
---
```

## Database

| Property | Value |
|---|---|
| ORM | SQLAlchemy 2.x |
| Dev default | SQLite `data/app.db` |
| Config | `settings.DATABASE_URL` |
| Init script | `python scripts/init_db.py` |

## Tables

| Table | Model | Dedup / Key |
|---|---|---|
| `advertisements` | `app.models.advertisement.Advertisement` | UNIQUE `bama_id` |
| `users` | `app.models.user.User` | UNIQUE `email` |
| `searches` | `app.models.search.Search` | FK `user_id` → users |

## Repositories

| Class | Module |
|---|---|
| `AdvertisementRepository` | `app.repositories.advertisement_repository` |
| `UserRepository` | `app.repositories.user_repository` |
| `SearchRepository` | `app.repositories.search_repository` |

### SearchRepository methods

| Method | Behavior |
|---|---|
| `list_for_user(user_id)` | all searches for user |
| `get_for_user(user_id, search_id)` | single owned search |
| `create(user_id, data)` | new filter |
| `update(search, data)` | patch fields |
| `delete(search)` | remove |
| `toggle_enabled(search)` | flip enabled flag |

## API Entry

| Property | Value |
|---|---|
| Run | `python run_api.py` |
| App module | `app.api.main:app` |
| Port | `8000` |
| Auth | JWT bearer |

## Env

| Variable | Default |
|---|---|
| `DATABASE_URL` | `sqlite:///data/app.db` |
| `JWT_SECRET_KEY` | dev placeholder |
| `CORS_ORIGINS` | `http://localhost:5173` |
