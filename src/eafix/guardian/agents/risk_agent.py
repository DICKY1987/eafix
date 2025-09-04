"""Risk agent placeholder."""

from dataclasses import dataclass


@dataclass
class RiskAgent:
    def assess(self) -> bool:
        return True
