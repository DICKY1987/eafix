"""Learning agent placeholder."""

from dataclasses import dataclass


@dataclass
class LearningAgent:
    def record(self, event: dict) -> None:
        pass
