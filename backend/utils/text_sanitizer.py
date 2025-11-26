"""Simple text sanitizer to reduce prompt injection and control chars."""

import re
from typing import Optional


def sanitize_user_text(text: Optional[str], max_length: int = 2000) -> str:
    """Strip control chars, trim length, and default to empty string."""
    if not text:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", str(text)).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned
