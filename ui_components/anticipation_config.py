"""Anticipation Configuration component placeholder."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class AnticipationConfig:
    """Stores anticipation hours and impact filters."""
    hours: List[int] = field(default_factory=lambda: [1, 2, 4, 8, 12])
    impacts: List[str] = field(default_factory=lambda: ["High", "Medium"])
