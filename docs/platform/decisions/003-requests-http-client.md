# ADR 003 — requests as HTTP Client

- Status: Accepted
- Date: 2026-08-30

## Context

نیاز به HTTP client با retry برای crawl پایدار.

## Decision

`requests` + `urllib3.Retry` via `HTTPAdapter` در `HttpClient`.

## Consequences

| ✅ | ❌ |
|---|---|
| mature ecosystem | sync-only (no async) |
| built-in retry adapter | heavier than httpx for async future |
| simple API | |

## Rejected Alternatives

- **httpx async** — complexity not needed yet
- **aiohttp** — async-first, overkill for current sequential crawl
- **urllib raw** — no retry/session ergonomics

> Behavior فعلی: [`current_state/modules.md`](../current_state/modules.md)
