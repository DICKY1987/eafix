"""Strategy ID generation utilities."""
from __future__ import annotations
import hashlib


def generate(country: str, impact: str, anticipation: bool = False) -> int:
    """Generate a simple numeric strategy identifier.

    The ID is derived from the country and impact strings with a checksum.
    Anticipation events receive an additional offset of 1000.
    """
    base = (country + impact).upper()
    checksum = int(hashlib.sha1(base.encode()).hexdigest(), 16) % 1000
    sid = checksum
    if anticipation:
        sid += 1000
    return sid
