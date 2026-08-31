# Schema — taxonomy & bootstrap metrics

```yaml
---
domain: application
authority: spec
owner: persistence
verify: project/src/app/models/taxonomy.py
---
```

## taxonomy_snapshots

Versioned extraction runs after each completed site-map crawl.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `source_job_id` | VARCHAR(36)? | crawl job that produced this snapshot |
| `schema_version` | INTEGER | extraction rule version (default 1) |
| `is_current` | BOOLEAN | only one snapshot is current at a time |
| `created_at` | TIMESTAMPTZ | |

## taxonomy_terms

User-facing catalog: brand, model, city labels with crawl URLs.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `snapshot_id` | FK → taxonomy_snapshots | |
| `section_key` | VARCHAR(64) | `car`, `motorcycle`, `truck` |
| `term_type` | VARCHAR(16) | `brand`, `model`, `city` |
| `parent_id` | FK → taxonomy_terms? | model → brand |
| `label` | VARCHAR(256) | Persian display name |
| `slug` | VARCHAR(128) | URL path segment |
| `listing_url` | VARCHAR(2048)? | canonical Bama listing URL |
| `page_key` | VARCHAR(64)? | reference to `site_nodes` |
| `is_active` | BOOLEAN | false when source page missing in new crawl |
| `meta` | JSON | `depth`, `page_type`, `path_parts` |
| `created_at` | TIMESTAMPTZ | |

## taxonomy_refs

Evidence for structure diff when Bama changes URLs.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `term_id` | FK → taxonomy_terms CASCADE | |
| `page_key` | VARCHAR(64)? | |
| `url` | VARCHAR(2048) | |
| `url_pattern` | VARCHAR(512)? | |
| `source_job_id` | VARCHAR(36)? | |
| `extracted_at` | TIMESTAMPTZ | |

## search_bootstrap_metrics

Per-search bootstrap discovery log for admin stats.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `search_id` | FK → searches CASCADE | |
| `job_id` | VARCHAR(36)? | |
| `listing_url` | VARCHAR(2048) | URL used for bootstrap |
| `pages_crawled` | INTEGER | |
| `ads_found` | INTEGER | |
| `ads_new` | INTEGER | |
| `matching_count` | INTEGER | ads matching filter after crawl |
| `created_at` | TIMESTAMPTZ | |

## Extraction

`TaxonomyBuilder` runs after `SiteMapProjectionBuilder` on completed site-map jobs. See [`site_map.md`](site_map.md).
