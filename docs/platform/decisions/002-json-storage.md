# ADR 002 — JSON File Storage

- Status: Accepted
- Date: 2026-08-30

## Context

نتایج crawl باید persist شوند. پروژه در فاز اولیه است — بدون requirement برای query یا concurrent writes.

## Decision

`JsonStorage` — یک فایل JSON per run با timestamp در نام فایل.

## Consequences

| ✅ | ❌ |
|---|---|
| zero infra setup | no query capability |
| human-readable output | not scalable for large volume |
| easy debug | no deduplication |

## Rejected Alternatives

- **SQLite** — premature for MVP
- **PostgreSQL** — requires infra not yet needed

> Contract فعلی: [`current_state/storage.md`](../current_state/storage.md)

> **Superseded for production persistence** by [ADR 005](005-relational-db-manual-schema.md) — JSON storage remains valid for Phase 0 scaffold only.
