# Scripts

Operator CLI tools for the Bama crawler backend. **Canonical rules:** [`docs/development/scripts.md`](../../docs/development/scripts.md).

| Script | Command |
|---|---|
| Initialize database | `python scripts/init_db.py` |
| Inspect crawled data & jobs | `python scripts/inspect_data.py` |
| Clear stuck crawl jobs | `python scripts/cleanup_stale_jobs.py` |

Run all commands from `project/` with `PYTHONPATH=src` or an activated venv that includes `src`.

Do not add ad-hoc debug scripts here — use `scripts/_scratch/` (gitignored) or pytest.
