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
| `match_id` | INTEGER FK | → matches.id |
| `user_id` | INTEGER FK | → users.id |
| `channel` | VARCHAR | `in_app`, `log`, `email`, … |
| `title` | VARCHAR | inbox title |
| `body` | TEXT | inbox body |
| `payload` | JSON | ad_url, search metadata |
| `status` | VARCHAR | `pending`, `sent`, `failed` |
| `read_at` | TIMESTAMPTZ | in-app read timestamp |
| `sent_at` | TIMESTAMPTZ | |
| `error` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

**Constraint:** `UNIQUE(match_id, channel)`
