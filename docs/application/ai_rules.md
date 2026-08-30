# Application AI Rules (L4)

```yaml
---
domain: application
authority: L4
owner: ai-contributor-application
not_authoritative_for:
  - platform API facts (→ platform/current_state/)
---
```

## Before Editing Application Code

1. Read [`current_state.md`](../current_state.md)
2. Read platform L1 for APIs you consume
3. Read [`spec/open_questions.md`](../spec/open_questions.md) for blockers

## Constraints

- **Do not** modify platform `core/` for site-specific needs — extend via new `*Crawler`
- **Do not** duplicate platform facts in application L1
- **Do not** document planned API in L1 — use `knowledge/` with maturity tag
- **Do not** add frontend framework without updating L1 + blueprint

## Site-Specific Crawler

```
project/src/crawler/my_site_crawler.py   # or application/crawlers/
  └── subclass BaseCrawler
  └── wire in main.py
```

Update: `application/current_state/entrypoint.md`

## Frontend Changes

When framework selected:

1. Update `application/current_state/frontend.md` (L1)
2. Update `application/spec/product_blueprint.md` (L5)
3. ADR if architectural (e.g. React vs Vue)

## Knowledge Promotion

| From | To | When |
|---|---|---|
| `knowledge/features/` working | L1 + code | feature shipped |
| `knowledge/vision/` input | spec/accepted | stakeholder sign-off |

## Learning Reports

Required for non-obvious decisions → `knowledge/learning_reports/`

Template: [`knowledge/learning_reports/TEMPLATE.md`](../knowledge/learning_reports/TEMPLATE.md)
