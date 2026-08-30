# چارچوب مستندسازی لایه‌ای — استخراج‌شده از RAG، قابل استفاده برای هر پروژه

این گزارش **طرز فکر** مستندسازی پروژه RAG/chatbot.ir را به اصول عمومی تبدیل می‌کند — بدون وابستگی به هوش مصنوعی، LangGraph، یا دامنه RAG. هدف: یک **سیستم دانش پروژه** بسازید که هم برای انسان قابل‌اتکا باشد، هم برای AI/ابزارها قابل مسیریابی.

---

## ۱. فلسفه پایه

### ۱.۱ Documentation-first (اول مستند، بعد کد)

قبل از هر تغییر یا تحلیل:

1. مستندات موجود را بخوانید
2. از آن‌ها به‌عنوان **نقشه اولیه** استفاده کنید
3. کد را فقط برای **تأیید یا کشف شکاف** بخوانید

> مستند «منبع حقیقت زنده» است — نه PDF قدیمی که بعد از release نوشته می‌شود.

### ۱.۲ تفکیک سه نوع دانش

| نوع | سؤال | مثال |
|---|---|---|
| **Fact** | الان چیست؟ | API، schema، flowهای ثبت‌شده |
| **Structure** | چطور به هم وصل است؟ | معماری، pipeline، dependency |
| **Decision** | چرا این‌طور شد؟ | ADR، trade-off، گزینه‌های ردشده |

**اشتباه رایج:** همه را در یک README طولانی قاطی کردن.

### ۱.۳ بدون حدس (No speculation)

فقط آنچه **قابل تأیید** است مستند شود:

- کد و تست
- کامنت/docstring
- مستند قبلی
- ورودی stakeholder (با برچسب maturity)

> «قرار است بسازیم» ≠ «الان هست». aspirational doc ممنوع.

### ۱.۴ هم‌زمانی کد و مستند (Co-evolution)

تغییر عمومی API/رفتار **ناقص** است تا L1 (واقعیت جاری) به‌روز نشود — در **همان PR/تغییر**.

---

## ۲. مدل Authority — پنج لایه (L1 تا L5)

| Level | نام | سؤال | منبع حقیقت؟ |
|---|---|---|---|
| **L1** | Canonical | **الان** چیست؟ | ✅ بله |
| **L2** | Reference | **چطور** به هم می‌خورد؟ | ❌ (راهنما) |
| **L3** | ADR | **چرا** این تصمیم؟ | ❌ (تاریخچه تصمیم) |
| **L4** | Rules | **چه محدودیت‌هایی** داریم؟ | محدودیت فقط |
| **L5** | Summary | جهت‌گیری سریع | ❌ (orientation) |

### قوانین طلایی

```
L1 = فقط fact — بدون تاریخ، نظر، tutorial
L3 = فقط why — هرگز API را از ADR استنتاج نکن
L5 = خلاصه اجرایی — نه جایگزین L1
```

**قانون supersede:** ADR قدیمی immutable است. تصمیم جدید → ADR جدید با status «Superseded by NNN». زنجیره supersede **API فعلی را تعریف نمی‌کند** — API فقط در L1 است.

---

## ۳. تفکیک Domain (Bounded Context)

| مفهوم RAG | معادل این پروژه |
|---|---|
| Platform / Core | `project/src/crawler/` — زیرساخت کرالر قابل استفاده مجدد |
| Application / Product | `project/main.py`، `ExampleCrawler`، `frontend/` — منطق محصول و UX |

### قوانین مرز

1. هر domain **پوشه docs خودش** را دارد
2. Application می‌تواند به Platform **لینک** بدهد (مصرف API)
3. Platform **هرگز** Application را spec نمی‌کند
4. سؤال cross-domain → **یک owner** در جدول authority

---

## ۴. Single Owner per Question (A3)

برای **هر سؤال** دقیقاً **یک فایل** مالک است.

| سؤال نمونه | Owner |
|---|---|
| کلاس‌ها و ماژول‌های platform کدام‌اند؟ | `platform/current_state/modules.md` |
| env vars کرالر چیست؟ | `platform/current_state/config.md` |
| entrypoint اپلیکیشن چیست؟ | `application/current_state/entrypoint.md` |
| چرا JSON storage نه DB؟ | `platform/decisions/002-json-storage.md` |
| قوانین coding | `development/development_rules.md` |

**اگر دو فایل یک fact را تکرار کنند → bug مستنداتی.**

---

## ۵. L1 — `current_state/` (قلب سیستم)

- فقط **fact**
- جدول، bullet، enum — نه prose بلند
- هر topic فایل جدا با `verify: <مسیر کد>`

### YAML header

```yaml
---
domain: platform | application | shared
authority: L1
owner: topic-name
verify: path/to/code
questions:
  - Which modules are registered?
not_authoritative_for:
  - why
  - tutorial
---
```

### سیاست رشد

| قانون | حد |
|---|---|
| Index (`current_state.md`) | ≤ 80 خط |
| هر topic file | ≤ 120 خط، fact only |
| overflow | فایل topic جدید |

### Read order (A0)

```
1. AUTHORITY.md
2. domain را انتخاب کن (platform یا application)
3. <domain>/current_state.md → current_state/*.md
4. technical/ یا architecture/ برای جزئیات
5. decisions/ فقط برای why
```

---

## ۶–۹. L2 تا L5

- **L2** (`architecture/`, `technical/`) — چطور سیستم کنار هم می‌آید
- **L3** (`decisions/`) — ADR، WHY only، immutable
- **L4** (`development_rules.md`, `ai_rules.md`, `AUTHORITY.md`) — محدودیت‌ها
- **L5** (`spec/`, `knowledge/`) — orientation و تعریف (نه runtime truth)

---

## ۱۰. Knowledge vs Runtime

```
knowledge/     = «چه می‌خواهیم بسازیم / تعریف / ورودی خام»
current_state/ = «الان چه ساخته شده»
```

| Maturity | می‌تواند کد را هدایت کند؟ |
|---|---|
| `input` | ❌ |
| `working` | ❌ تا promote |
| `accepted` | ✅ via L1/ADR/spec |
| `superseded` | ❌ |

---

## ۱۱–۱۴. Capability، Sync، Learning Report، Open Questions

جزئیات کامل در [`AUTHORITY.md`](AUTHORITY.md) و [`development/development_rules.md`](development/development_rules.md).

---

## ۱۵. Definition of Done (مستندات)

Task **تمام** نیست مگر:

- [ ] کد + test سبز
- [ ] L1 owner به‌روز (Rule A4)
- [ ] ADR اگر why عوض شد
- [ ] learning report اگر adoption/decision non-obvious
- [ ] open_questions اگر سؤالی بسته شد
- [ ] README اگر onboarding impact دارد

> **Stale doc = bug** — مثل test شکسته.

---

## ۱۶. Anti-patterns

| Anti-pattern | جایگزین |
|---|---|
| README 500 خطی | L1/L2/L3 split |
| ADR به‌عنوان API spec | L1 canonical |
| «به زودی می‌سازیم» در L1 | knowledge/working |
| duplicate fact در ۳ فایل | single owner A3 |
| doc بعد از merge | same PR (A4) |

---

## ۱۷. Cheat Sheet

```
L1 current_state  → WHAT IS (canonical, verify: code)
L2 architecture   → HOW IT FITS
L3 decisions      → WHY (immutable, never API)
L4 rules          → CONSTRAINTS
L5 spec/knowledge → ORIENTATION & DEFINITION

A3: one question → one owner file
A4: API change incomplete until L1 updated
heavy change → sync docs in same PR
no speculation · no aspirational docs · no duplicate
```

---

نسخه کامل methodology — مرجع تیم. برای owner table و read order عملی → [`AUTHORITY.md`](AUTHORITY.md).
