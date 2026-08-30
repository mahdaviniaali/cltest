# ADR-008: Site Map BFS + Inspector

## Status

Accepted

## Context

Bama incremental crawl (ADR-006) covers new ads on listing pages but not full site structure. We need:

- Full-site BFS discovery with loop prevention
- URL taxonomy and section classification (car, motorcycle, etc.)
- Persistent graph/tree in DB
- Live observability and admin inspector UI

## Decision

1. Add separate `CrawlJobType.SITE_MAP` — does not replace incremental crawl
2. Store site intelligence in DB tables: `site_nodes`, `site_edges`, `visited_urls`, `crawl_events`, `site_sections`
3. Lift URL identity/scope/pattern logic from site-map reference (pure functions, no hexagonal copy)
4. Bama structure config in `config/bama_site.yaml` (section hints, scope) — not hardcoded selectors
5. Inspector API at `/api/inspector/*` + frontend `/admin/inspector`
6. Celery task `crawl.site_map` on existing `crawl` queue
7. Optional Crawl4AI adapter behind `PageFetcher` port only (ADR-004)

## Consequences

- Two crawl modes coexist: incremental (production ads) + site map (discovery/ops)
- Site catalog can override `BAMA_LISTING_URL` via `listing_url_resolver`
- Full site BFS requires rate limits (`SITE_MAP_DELAY_SECONDS`) and page caps

## References

- site-map: `identity.py`, `discovery.py`, `infer_url_pattern`, inspector UI layout
- ADR-006, ADR-004
