# Site Map Schema

```yaml
---
domain: application
authority: spec
owner: persistence
verify: project/src/app/models/site_map.py
---
```

## Tables

### site_nodes

| Column | Type | Notes |
|---|---|---|
| page_key | PK string(64) | SHA256 of normalized URL |
| url | string | canonical fetch URL |
| url_pattern | string | inferred template |
| depth | int | BFS depth |
| parent_page_key | string? | parent in crawl tree |
| page_type | enum | hub, listing, detail, static, unknown |
| section | string? | car, motorcycle, truck, news, … |
| title, excerpt | string? | from page meta |
| status | enum | discovered, crawled, failed, skipped |
| content_hash | string? | SHA256 body |
| meta | JSON | link counts, etc. |

### site_edges

| Column | Type | Notes |
|---|---|---|
| from_page_key, to_page_key | string | UNIQUE pair |
| relation_type | string | internal_link, parent, sitemap |

### visited_urls

Frontier persistence for loop prevention and resume.

| Column | Type |
|---|---|
| url, page_key, job_id | |
| status | pending, crawled, failed, skipped |
| depth | int |

### crawl_events

Observability stream for inspector live feed.

### site_sections

Post-job aggregate catalog per detected section.

## crawl_jobs extensions

- `job_type`: `site_map`
- `status`: adds `paused`
- `pages_discovered`, `pages_failed`
