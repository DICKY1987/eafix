"""Simplified implementation of the guardian orchestrator.

The project this repository is based on contains an extensive "guardian"
sub‑system responsible for coordinating health checks and remediation actions.
Only a tiny portion of that functionality is required for the exercises in this
kata: the ability to run a basic check and to forward events and compliance log
messages to optional sub‑agents.  The implementation below purposely keeps the
behaviour minimal while providing a clean, testable API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .agents.learning_agent import LearningAgent
from .agents.compliance_agent import ComplianceAgent


@dataclass
class GuardianOrchestrator:
    """Coordinate health checks and remediation runbooks.

    Parameters
    ----------
    learning_agent:
        Optional agent used to record events that may later be analysed for
        continuous learning.
    compliance_agent:
        Optional agent used to log compliance related messages.
    """

    learning_agent: Optional[LearningAgent] = None
    compliance_agent: Optional[ComplianceAgent] = None

    def check(self) -> Dict[str, Any]:
        """Return a static OK result.

        Production code will evaluate constraints and gate logic.  The helper
        method exists so higher level components can depend on a stable API.
        """

        return {"status": "OK"}

    # ------------------------------------------------------------------
    def record_event(self, event: Dict[str, Any]) -> None:
        """Forward *event* to the learning agent if one is configured."""

        if self.learning_agent is not None:
            self.learning_agent.record(event)

    def log_compliance(self, message: str) -> None:
        """Forward a compliance log message to the compliance agent."""

        if self.compliance_agent is not None:
            self.compliance_agent.log(message)


__all__ = ["GuardianOrchestrator"]

