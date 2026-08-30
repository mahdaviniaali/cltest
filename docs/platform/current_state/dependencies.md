# Platform Dependencies

```yaml
---
domain: platform
authority: L1
owner: dependencies
verify: project/requirements.txt
questions:
  - What Python packages does the platform require?
not_authoritative_for:
  - why each was chosen (→ decisions/)
---
```

## requirements.txt

| Package | Min Version |
|---|---|
| `requests` | 2.31.0 |
| `beautifulsoup4` | 4.12.0 |
| `lxml` | 5.0.0 |
| `python-dotenv` | 1.0.0 |

## Usage in Code

| Package | Used by |
|---|---|
| `requests` | `HttpClient` |
| `beautifulsoup4` + `lxml` | `HtmlParser` |
| `python-dotenv` | `config/settings.py` |

## Python Version

3.10+ (type hints, `list[str]` compatible)
