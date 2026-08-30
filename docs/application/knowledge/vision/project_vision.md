# Project Vision

```yaml
---
domain: application
authority: L5
maturity: input
owner: vision
not_authoritative_for:
  - runtime state
  - committed roadmap dates
---
```

## Problem

کاربران Bama.ir می‌خواهند به‌محض publish آگهی جدید خودرو که با criteria آن‌ها match می‌کند، **notify** شوند — بدون refresh دستی مداوم.

## Target Users

- کاربر نهایی که search/filter تعریف می‌کند (via API)
- Operator/DevOps که crawl و notification را monitor می‌کند

## Success Criteria (Draft)

| Criterion | Measure |
|---|---|
| New ads detected | dedup + no duplicate records |
| Match accuracy | criteria correctly applied |
| No repeat notify | same ad + user + search once |
| Crawl resilience | graceful failure + retry |
| Deployable | Docker + K8s |
| Observable | logs + health baseline |

## Non-Goals (Current)

- Anti-bot / CAPTCHA bypass
- Real-time sub-second alerts (periodic crawl OK)
- Mobile native app

> **maturity: input** — cannot drive implementation until promoted to accepted.
