# Capability Map

```yaml
---
domain: application
authority: L5
maturity: working
owner: capabilities
not_authoritative_for:
  - runtime API (→ platform/current_state/)
---
```

## Model

```
Capability Domain ≠ Level ≠ Feature
Level = maturity within domain
Feature = concrete implementation
```

## Domains

| Domain | Job | Current Level | Features |
|---|---|---|---|
| **Fetch** | HTTP GET reliable | L1 | HttpClient, retry |
| **Parse** | HTML → structured | L1 | HtmlParser, ExampleCrawler.parse |
| **Store** | persist results | L1 | JsonStorage |
| **Orchestrate** | run crawl jobs | L1 | BaseCrawler.crawl, main.py |
| **Schedule** | timed/recurring runs | L0 | — |
| **Serve** | expose data to UI | L0 | — |
| **Present** | user interface | L0 | frontend scaffold |

## Level Key

| Level | Meaning |
|---|---|
| L0 | not implemented |
| L1 | baseline MVP |
| L2 | enhanced |
| L3 | mature/production-grade |

## Dependency Graph

```
Present → Serve → Store
Orchestrate → Fetch → Parse → Store
Schedule → Orchestrate
```

## Contract Template (per domain)

```
Job: ...
Input: ...
Output: ...
Guarantee: ...
```

> Promote to `accepted` when contracts are signed off → then mirror facts in L1.
