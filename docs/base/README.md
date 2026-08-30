# Base Documents — اسناد پایه پروژه

```yaml
---
domain: shared
authority: L5
maturity: working
owner: base-docs-index
intent: explain
questions:
  - اسناد پایه پروژه کجا هستند؟
  - ترتیب خواندن قبل از معماری و پیاده‌سازی چیست؟
not_authoritative_for:
  - runtime facts (→ */current_state/)
  - API canonical (→ L1)
---
```

اسناد **cross-domain** که قبل از هر تصمیم معماری یا پیاده‌سازی خوانده می‌شوند.

## Read Order (قبل از کد)

```
1. تعریف_پروژه.md     ← پروژه چیست / چه نیست
2. رویکرد_پروژه.md    ← چطور می‌سازیم / فازها / گیت‌ها
3. AUTHORITY.md       ← مدل authority
4. domain docs        ← platform | application
```

## Files

| سند | نقش | maturity |
|---|---|---|
| [`تعریف_پروژه.md`](تعریف_پروژه.md) | Freeze/Explain — مرز محصول، خروجی، scope | working |
| [`رویکرد_پروژه.md`](رویکرد_پروژه.md) | Explain — روش کار، فازها، گیت تصمیم | working |

## Relation to Other Layers

```text
base/ (L5)           → WHAT & HOW WE BUILD (orientation)
application/spec/    → blueprint, open questions, decisions
*/current_state/     → WHAT IS (canonical, verify: code)
*/architecture/      → HOW IT FITS (structure)
*/decisions/         → WHY (ADR)
```

> **قانون:** base doc نمی‌تواند جای L1 را بگیرد. تا promote نشود، implementation را lock نمی‌کند.
