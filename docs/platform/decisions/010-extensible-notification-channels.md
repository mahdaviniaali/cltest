# ADR 010 — Extensible Notification Channels

- Status: Accepted
- Date: 2026-08-31
- Closes: [OQ-006](../../application/spec/open_questions.md)

## Context

The spec requires at least one notification channel with idempotent delivery and extensibility for Email, SMS, Telegram, and Webhook without changing crawler or matching logic.

Phase 3 prioritizes **in-app inbox** as the primary user-visible channel while keeping external channels pluggable.

## Decision

### 1. Event-driven orchestration

Existing outbox event `notify.requested` triggers Celery task `notify.orchestrate(match_id)`.

`NotificationOrchestrator`:

1. Loads match, search, user, ad
2. Builds `NotificationMessage`
3. Resolves channels via `ChannelPolicy` (env master switch + user preferences)
4. Upserts one delivery row per `(match_id, channel)`
5. Dispatches channel adapters

### 2. Multi-channel deliveries

Table `notifications` uses `UNIQUE(match_id, channel)` and inbox fields: `title`, `body`, `payload`, `read_at`.

### 3. Channel adapters (port/adapter)

| Channel | Phase 3 |
|---|---|
| `in_app` | Primary — persisted inbox + UI bell |
| `log` | Dev/diagnostic |
| `email`, `sms`, `telegram` | Stub adapters — enabled only when env + user fields present |

Add a new channel by implementing `NotificationChannel` and registering in `ChannelRegistry`.

### 4. User preferences (schema only)

`users.notification_channels` JSON default `["in_app"]`. Full UC-N3 UI deferred.

## Consequences

| Pros | Cons |
|---|---|
| Matching/crawler unchanged | External channels need future wiring |
| Idempotent per channel | SQLite migration recreates notifications table |
| In-app UX immediate | Poll-based inbox (no WebSocket in v1) |

## Related

- [007-transactional-outbox-celery.md](007-transactional-outbox-celery.md)
- [matches_notifications.md](../../application/spec/schema/matches_notifications.md)
