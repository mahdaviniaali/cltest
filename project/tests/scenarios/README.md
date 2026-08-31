# Product Scenario Tests

Acceptance tests from the **user/product perspective** — not technical unit tests.

Run:

```bash
pytest tests/scenarios/ -m product -v
```

## UC index

| Scenario | UC | File |
|---|---|---|
| A1 | UC-U1 register/login | `test_auth_journey.py` |
| A8 | UC-U1 isolation | `test_auth_journey.py` |
| A2 | UC-U2 create filter | `test_filter_journey.py` |
| A3 | UC-U7 multiple filters | `test_filter_journey.py` |
| A4 | UC-U3 list filters | `test_filter_journey.py` |
| A5 | UC-U4 edit filter | `test_filter_journey.py` |
| A6 | UC-U5 delete filter | `test_filter_journey.py` |
| A7, A7b | UC-U6 toggle | `test_filter_journey.py` |
| B1–B7, B9 | cache-first / ADR-011 | `test_cache_first_journey.py` |
| B8 | shared fingerprint job | `test_multi_user_journey.py` |
| C1–C9 | UC-M1..M3 matching | `test_matching_journey.py` |
| D1–D6 | UC-N1..N2 notifications | `test_notification_journey.py` |
| E1–E3 | multi-user / ADR-011 | `test_multi_user_journey.py` |
| F1–F2 | E2E (تعریف_پروژه) | `test_end_to_end_journey.py` |

**Total: 38 scenarios**

## Structure

```text
tests/scenarios/
├── conftest.py          # ali/sara clients, scenario_db
├── helpers/
│   ├── scenario_factory.py
│   ├── scenario_steps.py
│   └── scenario_assertions.py
└── test_*_journey.py
```

## Conventions

- Docstring فارسی + Given/When/Then
- Mock only external crawl dispatch (`dispatch_on_demand_job`)
- Matching/notify pipelines run synchronously in-process for product assertions

Technical tests (parsers, URL identity, crawl policy) stay in `tests/test_*.py`.
