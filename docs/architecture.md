# Architecture

## Overview

پروژه از سه بخش اصلی تشکیل شده است:

| بخش | مسیر | مسئولیت |
|-----|------|---------|
| Crawler | `project/` | جمع‌آوری و پردازش داده از وب |
| Frontend | `frontend/` | نمایش و مدیریت داده‌ها |
| Docs | `docs/` | مستندات فنی و راهنما |

## Crawler Layers

```
main.py
  └── crawler.core.base_crawler.BaseCrawler
        ├── crawler.core.http_client.HttpClient
        ├── crawler.parsers.*        (HTML/JSON parsers)
        ├── crawler.storage.*        (save results)
        └── crawler.utils.*          (helpers)
```

## Data Flow

1. `main.py` تنظیمات را از `config/settings.py` می‌خواند.
2. `BaseCrawler` URLها را از صف می‌گیرد و با `HttpClient` درخواست می‌زند.
3. Parser خروجی را پردازش می‌کند.
4. Storage نتیجه را ذخیره می‌کند (JSON فایل یا دیتابیس).

## Dependencies

- **requests** — HTTP client
- **beautifulsoup4** — HTML parsing
- **lxml** — fast XML/HTML parser backend
