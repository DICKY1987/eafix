"""Strategy ID component placeholder."""
from dataclasses import dataclass, field
from typing import List
from strategy_id import generate


@dataclass
class StrategyIDs:
    """Manages generated strategy IDs."""
    ids: List[int] = field(default_factory=list)

    def add(self, country: str, impact: str, anticipation: bool = False) -> int:
        sid = generate(country, impact, anticipation)
        if sid in self.ids:
            raise ValueError("duplicate strategy id")
        self.ids.append(sid)
        return sid
