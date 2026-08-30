from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from celery import Celery
from celery.schedules import schedule

from config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "cltest",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.crawl",
        "app.workers.tasks.outbox",
        "app.workers.tasks.match",
        "app.workers.tasks.notify",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_default_queue="default",
    task_routes={
        "crawl.*": {"queue": "crawl"},
        "outbox.*": {"queue": "outbox_relay"},
        "match.*": {"queue": "match"},
        "notify.*": {"queue": "notify"},
    },
    beat_schedule={
        "scheduled-incremental-crawl": {
            "task": "crawl.scheduled_incremental",
            "schedule": schedule(run_every=settings.CRAWL_INTERVAL_SECONDS),
        },
        "outbox-relay": {
            "task": "outbox.relay",
            "schedule": schedule(run_every=30.0),
        },
    },
)
