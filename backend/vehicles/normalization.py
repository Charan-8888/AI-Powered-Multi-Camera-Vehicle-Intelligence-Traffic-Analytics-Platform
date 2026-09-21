"""Shared normalization for registration numbers crossing API boundaries."""

import re


def normalize_plate(value: str) -> str:
    """Return a canonical uppercase, alphanumeric plate identifier."""
    return re.sub(r'[^A-Z0-9]', '', value.upper())
