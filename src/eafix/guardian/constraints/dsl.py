"""Tiny DSL parser placeholder for constraints."""

from __future__ import annotations

from typing import Any, Dict


def evaluate(expression: str, context: Dict[str, Any]) -> bool:
    """Very small eval wrapper used only for tests.

    WARNING: uses Python's eval and therefore must not be used in
    production without proper sandboxing.
    """
    try:
        return bool(eval(expression, {}, context))
    except Exception:
        return False

