# ADR 001 — Layered Crawler Architecture

- Status: Accepted
- Date: 2026-08-30

## Context

کرالر باید برای سایت‌های مختلف قابل extend باشد بدون copy-paste منطق HTTP و storage.

## Decision

ساختار لایه‌ای:

- `core/` — orchestration + HTTP
- `parsers/` — HTML extraction (pure)
- `storage/` — persistence
- `utils/` — cross-cutting helpers

Application layer (`main.py`, custom crawlers) composition root است.

## Consequences

| ✅ | ❌ |
|---|---|
| clear extension points | more files than monolith |
| testable parsers | indirection for tiny scripts |
| reusable across products | initial learning curve |

## Rejected Alternatives

- **Monolithic script** — not reusable, hard to test parsers
- **Scrapy framework** — heavier dependency for current scope *(superseded by ADR 004 — adopted as infrastructure adapter, not architecture core)*

> API فعلی: [`current_state/modules.md`](../current_state/modules.md)
