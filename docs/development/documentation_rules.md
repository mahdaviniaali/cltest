# Documentation Writing Rules

```yaml
---
domain: shared
authority: L4
owner: documentation-rules
not_authoritative_for:
  - runtime facts
---
```

راهنمای عملی نوشتن مستند — مکمل [`METHODOLOGY.md`](../METHODOLOGY.md).

## قبل از نوشتن

1. [`AUTHORITY.md`](../AUTHORITY.md) → owner فایل را پیدا کن (A3)
2. لایه authority را تشخیص بده (L1–L5)
3. کد را برای `verify:` بخوان — **no speculation**

## انتخاب لایه

| می‌خواهی بنویسی… | برو به… |
|---|---|
| «الان API چیست» | L1 `current_state/*.md` |
| «pipeline چطور boot می‌شود» | L2 `architecture/` |
| «چرا PostgreSQL نه Mongo» | L3 `decisions/` (ADR جدید) |
| «چه کار نکن» | L4 `development_rules.md` یا `ai_rules.md` |
| «vision / roadmap / feature draft» | L5 `knowledge/` یا `spec/` |

## قالب L1 Topic File

```markdown
# Topic Title

\`\`\`yaml
---
domain: platform | application | shared
authority: L1
owner: topic-id
verify: path/to/code.py
questions:
  - Which ...?
not_authoritative_for:
  - why
  - tutorial
---
\`\`\`

## Section (facts only)

| Col | Col |
|---|---|
| fact | value |
```

### قوانین L1

- ✅ جدول، bullet، enum
- ✅ `verify:` در header
- ❌ prose بلند
- ❌ «به زودی»، «قرار است»
- ❌ تاریخچه تصمیم
- ❌ tutorial step-by-step

## قالب ADR (L3)

```markdown
# ADR NNN — Title
- Status: Proposed | Accepted | Deprecated | Superseded by MMM
- Date: YYYY-MM-DD

## Context
## Decision
## Consequences

> API فعلی: link to L1
```

- ADR accepted = **immutable**
- هرگز API را از ADR استنتاج نکن

## Knowledge Maturity Tags

```yaml
maturity: input | working | reference | accepted | superseded
```

| Tag | در L1 بگذار؟ |
|---|---|
| input | ❌ |
| working | ❌ |
| accepted | ✅ بعد از promote + کد |

## Promotion Checklist

وقتی `working` → `accepted`:

1. Fact → `current_state/` + کد (same PR)
2. Why → ADR
3. Register → `decision_register.md`
4. Phase → `product_blueprint.md`
5. Close → `open_questions.md`

## Size Limits

| File | Max |
|---|---|
| `current_state.md` | 80 lines |
| `current_state/*.md` | 120 lines |

Overflow → فایل topic جدید.

## Sync Policy

| Change Type | Action |
|---|---|
| public API change | L1 update (heavy) |
| new env var | L1 config + `.env.example` |
| structure change | L2 architecture |
| why change | new ADR |
| typo | skip doc sync (light) |

## Anti-patterns

| ❌ Don't | ✅ Do |
|---|---|
| duplicate fact in README + L1 | single owner |
| aspirational in L1 | knowledge/working |
| edit accepted ADR | new ADR supersede |
| infer API from ADR | read L1 |
| doc after merge | same PR |

## AI Contributors

- Read [`platform/ai_rules.md`](../platform/ai_rules.md)
- Read [`application/ai_rules.md`](../application/ai_rules.md)
- YAML header helps machine routing — always include on L1/L4
