# گزارش — Adoption of Layered Documentation Framework

- تاریخ: 2026-08-30
- مرحله: Phase 0 scaffold
- domain: shared
- نویسنده: team

## ۱. هدف

پیاده‌سازی سیستم مستندسازی لایه‌ای (L1–L5) برای پروژه کرالر — generalized از RAG/chatbot.ir methodology.

## ۲. از منبع مرجع چه خواندم

چارچوب مستندسازی لایه‌ای RAG:

- تفکیک Fact / Structure / Decision
- Authority layers L1–L5
- Single owner per question (A3)
- Co-evolution with code (A4)
- Knowledge maturity model (input → accepted → L1)

## ۳. اصول استخراج‌شده

1. L1 = canonical runtime truth — verify با کد
2. ADR = why only — immutable
3. knowledge/ ≠ current_state/
4. Platform/Application bounded context
5. Heavy change → doc sync same PR

## ۴. تصمیم پیاده‌سازی ما + چرا

| Decision | Why |
|---|---|
| `docs/platform/` + `docs/application/` | maps to `project/src/crawler/` vs `main.py`+`frontend/` |
| Retroactive ADR 001–003 | capture existing scaffold decisions |
| `METHODOLOGY.md` + `AUTHORITY.md` | methodology reference + operational owner table |
| YAML headers on L1/L4 files | AI-readable metadata |

## ۵. گزینه‌های ردشده

- **Single flat docs/ folder** — no authority separation, duplicate facts
- **README-only docs** — anti-pattern per methodology
- **Wiki external** — drift from code, not co-located

## ۶. اثر روی ساختار

```
docs/
├── AUTHORITY.md, METHODOLOGY.md, README.md
├── development/
├── platform/   (L1–L4)
└── application/ (L1–L5 + knowledge/)
```

Removed: flat `docs/architecture.md`, `docs/setup.md` → migrated to layered owners.

## ۷. تعارض با ADR/contract؟

None — documentation-only change.

## ۸. سنجش

- [ ] Every L1 file has `verify:` path
- [ ] Owner table covers all current questions
- [ ] No duplicate facts between old and new docs

## ۹. ۳ خط برای به خاطر سپردن

1. L1 بگو «الان چیست» — ADR بگو «چرا».
2. یک سؤال = یک فایل owner.
3. knowledge/input هرگز جایگزین L1 نیست.
