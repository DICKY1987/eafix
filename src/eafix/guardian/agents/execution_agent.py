"""Execution agent placeholder."""

from dataclasses import dataclass


@dataclass
class ExecutionAgent:
    def execute(self, order: dict) -> bool:
        return True
