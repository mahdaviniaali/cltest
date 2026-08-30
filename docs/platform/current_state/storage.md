# Platform Storage

```yaml
---
domain: platform
authority: L1
owner: storage
verify: project/src/crawler/storage/json_storage.py
questions:
  - How are crawl results persisted?
not_authoritative_for:
  - why JSON not database
---
```

## JsonStorage

| Property | Value |
|---|---|
| Constructor | `JsonStorage(output_dir: Path)` |
| Creates dir | yes, `mkdir(parents=True, exist_ok=True)` |

## save() Contract

| Param | Type | Default |
|---|---|---|
| `data` | `List[Any]` | required |
| `filename` | `str` | `"results"` |

## Output File Pattern

```
{output_dir}/{filename}_{timestamp}.json
```

| Part | Format |
|---|---|
| `timestamp` | UTC `%Y%m%d_%H%M%S` |
| encoding | UTF-8 |
| JSON | `ensure_ascii=False`, `indent=2` |

## Return Value

`Path` to written file.

## Current Backends

| Backend | Status |
|---|---|
| JSON file | ✅ implemented |
| Database | ❌ not implemented |
