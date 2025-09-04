"""System agent placeholder."""

from dataclasses import dataclass


@dataclass
class SystemAgent:
    def metrics(self) -> dict:
        return {}
