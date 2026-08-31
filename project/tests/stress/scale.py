"""Stress test scale presets — override with STRESS_SCALE=light|heavy."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StressScale:
    ads: int
    searches: int
    api_requests: int
    matching_searches: int
    crawl_ads: int
    concurrent_workers: int


_SCALES: dict[str, StressScale] = {
    "light": StressScale(
        ads=500,
        searches=50,
        api_requests=200,
        matching_searches=100,
        crawl_ads=200,
        concurrent_workers=20,
    ),
    "heavy": StressScale(
        ads=5000,
        searches=300,
        api_requests=2000,
        matching_searches=300,
        crawl_ads=2000,
        concurrent_workers=40,
    ),
}


def get_stress_scale() -> StressScale:
    name = os.getenv("STRESS_SCALE", "light").lower()
    if name not in _SCALES:
        raise ValueError(f"Unknown STRESS_SCALE={name!r}; use light or heavy")
    return _SCALES[name]
