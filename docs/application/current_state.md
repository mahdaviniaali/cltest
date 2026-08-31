# Application — Current State Index

```yaml
---
domain: application
authority: L1
owner: application-index
verify: project/main.py
not_authoritative_for:
  - platform API (→ platform/current_state/)
  - why (→ decisions/)
---
```

## Topics

| Topic | Owner | verify |
|---|---|---|
| Entrypoint & run flow | [`current_state/entrypoint.md`](current_state/entrypoint.md) | `project/main.py` |
| API routes (searches, taxonomy, inspector stats) | [`current_state/api.md`](current_state/api.md) | `project/src/app/api/` |
| Persistence (advertisements, taxonomy) | [`current_state/persistence.md`](current_state/persistence.md) | `project/src/app/` |
| Frontend status | [`current_state/frontend.md`](current_state/frontend.md) | `frontend/` |

## Platform Dependency

Application consumes platform public API — canonical spec در [`platform/current_state/`](../platform/current_state/).

## L5 References

- [`spec/product_blueprint.md`](spec/product_blueprint.md)
- [`spec/open_questions.md`](spec/open_questions.md)
- [`knowledge/vision/project_vision.md`](knowledge/vision/project_vision.md)

## L2 References

- [`architecture/overview.md`](architecture/overview.md)
