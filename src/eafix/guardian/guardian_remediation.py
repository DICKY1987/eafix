"""Remediation runbook placeholders for Guardian."""

from __future__ import annotations

from typing import Dict


def remediation_actions() -> Dict[str, str]:
    """Return mapping of remediation identifiers to descriptions.

    In the full implementation this would trigger scripts or workflows.
    """
    return {"noop": "No action"}

