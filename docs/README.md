# Documentation Router

سیستم دانش پروژه کرالر — documentation-first.

## Read Order (A0)

```
1. AUTHORITY.md                    — مدل authority + owner table
2. METHODOLOGY.md                  — فلسفه و cheat sheet
3. development/getting_started.md  — onboarding
4. domain انتخاب کن ↓
```

## Domains

| Domain | Index | کد |
|---|---|---|
| Platform (کرالر core) | [`platform/current_state.md`](platform/current_state.md) | `project/src/crawler/` |
| Application (محصول) | [`application/current_state.md`](application/current_state.md) | `project/main.py`, `frontend/` |

## Quick Links

| نیاز | برو به |
|---|---|
| setup محیط | [`development/getting_started.md`](development/getting_started.md) |
| قوانین coding | [`development/development_rules.md`](development/development_rules.md) |
| قوانین مستندنویسی | [`development/documentation_rules.md`](development/documentation_rules.md) |
| معماری platform | [`platform/architecture/overview.md`](platform/architecture/overview.md) |
| معماری application | [`application/architecture/overview.md`](application/architecture/overview.md) |
| چرا JSON storage؟ | [`platform/decisions/002-json-storage.md`](platform/decisions/002-json-storage.md) |
| blueprint محصول | [`application/spec/product_blueprint.md`](application/spec/product_blueprint.md) |
| سوالات باز | [`application/spec/open_questions.md`](application/spec/open_questions.md) |

## Authority Cheat Sheet

```
L1 current_state/  → WHAT IS
L2 architecture/   → HOW IT FITS
L3 decisions/      → WHY
L4 rules           → CONSTRAINTS
L5 spec/knowledge/ → ORIENTATION
```

## Contributing Docs

1. fact جدید → L1 owner (A3)
2. why جدید → ADR جدید (L3)
3. تعریف/vision → knowledge/ با maturity tag
4. heavy change → sync در همان PR (A4)

جزئیات: [`development/development_rules.md`](development/development_rules.md)
