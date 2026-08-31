# Project Scripts

```yaml
---
domain: shared
authority: L4
owner: scripts
verify: project/scripts/
questions:
  - Which CLI scripts are supported?
  - Where do ad-hoc debug scripts go?
not_authoritative_for:
  - pytest suite (→ project/tests/)
  - API/worker entrypoints (→ application/current_state/)
---
```

## Purpose

`project/scripts/` holds **operator-facing CLI tools** for setup, inspection, and recovery. It is not a dumping ground for one-off debug files.

## Supported scripts

| Script | When to use |
|---|---|
| `init_db.py` | First-time DB setup or empty `data/app.db` |
| `inspect_data.py` | Health check; table counts via `StatsService`; `--reclassify` fixes all node labels + rebuilds sections |
| `cleanup_stale_jobs.py` | UI stuck on «در حال بروزرسانی» — clear zombie `running`/`pending` jobs |

Run from `project/`:

```bash
python scripts/init_db.py
python scripts/inspect_data.py
python scripts/inspect_data.py --reclassify   # fix legacy page_type/section on all site_nodes
python scripts/cleanup_stale_jobs.py          # respect CRAWL_JOB_STALE_SECONDS
python scripts/cleanup_stale_jobs.py --force  # fail/cancel all in-flight jobs now
```

## Organization rules

1. **Only committed, named tools** live in `project/scripts/`. No `test_*.py`, `diag_*.py`, or `check_*` scratch files in this folder.
2. **Ad-hoc debugging** → delete after use, or keep under `project/scripts/_scratch/` (gitignored). Do not commit scratch scripts.
3. **Automated tests** → `project/tests/` (pytest), not `scripts/`.
4. **Smoke / E2E** → pytest or documented manual API steps; not loose scripts in repo root.
5. **New script checklist** — add only if it will be reused by operators:
   - module docstring + `main()` + `if __name__ == "__main__"`
   - entry in this file and `project/scripts/README.md`
   - no hardcoded user emails or search IDs

## Anti-patterns

| Bad | Good |
|---|---|
| `check_search2.py` tied to one DB row | `inspect_data.py --search-id 2` or SQL in inspect |
| ten copy-paste `test_*_live.py` | one pytest integration test |
| script left after debugging session | delete or move to `_scratch/` |

## Related

- DB init: [`application/current_state/persistence.md`](../application/current_state/persistence.md)
- Job stale recovery: `CrawlJobRepository.reconcile_stale_running_jobs` in app code; `cleanup_stale_jobs.py` for manual ops
