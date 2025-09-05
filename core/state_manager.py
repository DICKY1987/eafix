"""Simplified application state manager used for risk-gated commands.

The real project likely contains a complex state manager dealing with risk
policies and user preferences.  For the purposes of tests in this kata we only
need a minimal API offering :func:`is_action_allowed` which the command palette
uses to decide whether certain commands may run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class RiskState:
    """Represents the current risk gating state."""

    enabled: bool = True
    reason: str = ""


class StateManager:
    """Very small state manager tracking risk gating."""

    def __init__(self) -> None:
        self._risk_state = RiskState()

    # ------------------------------------------------------------------ risk
    def set_risk_gate(self, enabled: bool, reason: str = "") -> None:
        """Enable or disable the risk gate."""
        self._risk_state.enabled = enabled
        self._risk_state.reason = reason

    def is_action_allowed(self) -> Tuple[bool, str]:
        """Return ``(allowed, reason)`` for executing a risk-gated command."""
        if self._risk_state.enabled:
            return True, ""
        return False, self._risk_state.reason or "risk gate disabled"


# Expose a global instance similar to the real application
state_manager = StateManager()

__all__ = ["StateManager", "state_manager", "RiskState"]
