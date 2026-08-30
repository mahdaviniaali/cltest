# Schema — matches & notifications

```yaml
---
domain: application
authority: L5
maturity: working
owner: schema-matching
source: ADR 005, ADR 007
---
```

## matches

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `ad_id` | INTEGER FK | → advertisements.id |
| `search_id` | INTEGER FK | → searches.id |
| `matched_at` | TIMESTAMPTZ | |

**Constraint:** `UNIQUE(ad_id, search_id)`

## notifications

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `match_id` | INTEGER FK UNIQUE | → matches.id |
| `user_id` | INTEGER FK | → users.id |
| `channel` | VARCHAR | e.g. `log` (MVP) |
| `status` | VARCHAR | `pending`, `sent`, `failed` |
| `sent_at` | TIMESTAMPTZ | |
| `error` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

Idempotency: one notification row per match.
