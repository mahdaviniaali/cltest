# Development Rules (L4)

```yaml
---
domain: shared
authority: L4
owner: engineering-standards
not_authoritative_for:
  - runtime facts (→ L1)
  - architectural why (→ L3)
---
```

## Documentation Rules

### A3 — Single Owner

هر fact دقیقاً **یک** فایل owner دارد. duplicate = bug.

### A4 — Co-evolution

تغییر public API/behavior بدون به‌روزرسانی L1 **ناقص** است — در همان PR.

### Layer Discipline

| Layer | مجاز | ممنوع |
|---|---|---|
| L1 | fact، enum، جدول | why، tutorial، «به زودی» |
| L2 | structure، flow، setup | canonical values |
| L3 | context، decision، consequences | API spec |
| L4 | constraints، DoD | runtime state |
| L5 | vision، blueprint | جایگزین L1 |

### YAML Header

هر فایل L1/L4 باید header داشته باشد:

```yaml
---
domain: platform | application | shared
authority: L1 | L2 | L3 | L4 | L5
owner: topic-id
verify: path/to/code        # L1 only
questions:
  - ...
not_authoritative_for:
  - ...
---
```

### Size Caps

| فایل | حد |
|---|---|
| `current_state.md` (index) | ≤ 80 خط |
| `current_state/*.md` (topic) | ≤ 120 خط |
| overflow | فایل topic جدید |

### Heavy vs Light

**Heavy** (sync اجباری):
- public API / contract change
- config/env جدید یا تغییر
- flow/feature جدید
- ADR / promotion knowledge

**Light** (skip):
- typo، format
- internal helper بدون contract
- test fixture بدون behavior change

### PR Checklist

```
- [ ] heavy vs light?
- [ ] L1 owner updated?
- [ ] ADR if why changed?
- [ ] learning report if non-obvious adoption?
- [ ] open_questions if question closed?
- [ ] verify: claims match code?
```

## Code Rules

### Platform (`project/src/crawler/`)

- `BaseCrawler.parse()` abstract — extend در application layer
- `HttpClient` تنها نقطه HTTP — retry در همین لایه
- Parser pure function روی HTML string — بدون side effect
- Storage interface ساده — فعلاً JSON file

### Application

- `main.py` = composition root — wiring only
- crawler اختصاصی در `example_crawler.py` یا فایل جدید
- frontend جدا — بدون import مستقیم از crawler در browser

### Style

- Python 3.10+ type hints
- `logging` نه `print`
- env vars via `python-dotenv` — نه hardcode secret

## Definition of Done

Task تمام نیست مگر:

- [ ] کد کار می‌کند
- [ ] L1 owner به‌روز (A4)
- [ ] ADR اگر why عوض شد
- [ ] learning report اگر decision non-obvious
- [ ] README اگر onboarding عوض شد

> **Stale doc = bug**

## Anti-patterns

| ❌ | ✅ |
|---|---|
| fact در README ریشه | L1 topic file |
| API از ADR استنتاج | L1 canonical |
| aspirational در L1 | knowledge/working |
| doc بعد از merge | same PR |
