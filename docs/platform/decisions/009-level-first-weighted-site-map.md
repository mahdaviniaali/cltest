# ADR-009: Level-First Weighted Site Map Crawl

## Status

Accepted

## Context

Site map BFS (ADR-008) flooded the queue from sitemap.xml at depth 0, preventing breadth-first discovery of all sections (car, motorcycle, truck) before deep taxonomy. Page roles and crawl weights were partially hardcoded in `page_classifier.py`.

Site map scope must remain structural mapping only — ad detail parsing belongs to incremental crawl (ADR-006).

## Decision

1. **Level-first priority queue:** `sort_key = (depth, -weight, seq)` — complete each BFS level before going deeper; weight breaks ties within a level only.
2. **Config-driven routes:** `route_rules` and `section_roots` in `config/bama_site.yaml` define `role`, `weight`, and `priority` — no hardcoded detail regex in the crawl loop.
3. **Loop prevention:** canonical URL (`strip_query_params`) → `page_key`; `visited_urls` + queued set; monotonic BFS depth (`child.depth = parent.depth + 1`).
4. **Sitemap cap:** max `sitemap_max_urls` enqueued at depth 1 after homepage; remainder deferred until level 1 completes.
5. **Boundary:** site map stores `page_role` and `url_pattern` in catalog; incremental crawl consumes catalog for listing/detail targets — no `BamaDetailParser` in site map loop.

## Consequences

- Depth distribution reflects true BFS levels (0=home, 1=sections, 2+=taxonomy).
- Changing crawl priority is a YAML edit, not a code deploy.
- Inspector shows `current_depth`, `level_completed` events, and per-level section coverage.

## References

- ADR-008 (site map + inspector)
- ADR-006 (incremental crawl boundary)
- `crawler/domain/link_scorer.py`, `crawler/application/site_map_crawl.py`
