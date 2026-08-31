from __future__ import annotations

import re
from typing import Optional

_TRAILING_LABEL_PUNCT = re.compile(r"[\s،,]+$")


def normalize_label(value: Optional[str]) -> Optional[str]:
    """Strip trailing punctuation Bama often appends to brand/model labels."""
    if value is None:
        return None
    cleaned = _TRAILING_LABEL_PUNCT.sub("", value.strip())
    return cleaned or None
