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

جمع‌آوری structured data از وب به‌صورت repeatable و قابل مشاهده.

## Target Users

- Developer که crawl script می‌نویسد
- Operator که نتایج را monitor می‌کند (via future UI)

## Success Criteria (Draft)

| Criterion | Measure |
|---|---|
| Reliable fetch | retry + logging |
| Extensible parsers | new site < 1 day |
| Observable output | JSON + future UI |

## Non-Goals (Current)

- Distributed crawl cluster
- Real-time streaming
- CAPTCHA bypass

> **maturity: input** — cannot drive implementation until promoted to accepted.
