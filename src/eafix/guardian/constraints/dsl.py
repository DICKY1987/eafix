"""Tiny DSL parser placeholder for constraints.

This module originally used Python's :func:`eval` which allows execution of
arbitrary code.  To harden the system against code injection the evaluation is
now performed using the :mod:`ast` module and a very small interpreter that
supports only a limited subset of Python expressions (boolean operations,
comparisons and arithmetic on literal values).

The implementation intentionally raises ``ValueError`` for any unsupported
syntax to avoid accidentally executing unsafe constructs.
"""

from __future__ import annotations

from typing import Any, Dict

import ast
import operator


_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _safe_eval(node: ast.AST, context: Dict[str, Any]) -> Any:
    """Recursively evaluate a subset of Python AST nodes."""

    if isinstance(node, ast.Expression):
        return _safe_eval(node.body, context)

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        return context[node.id]

    if isinstance(node, ast.BoolOp):
        values = [_safe_eval(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ValueError("Unsupported boolean operator")

    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand, context)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.Not):
            return not operand
        raise ValueError("Unsupported unary operator")

    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left, context)
        right = _safe_eval(node.right, context)
        op_type = type(node.op)
        if op_type in _BIN_OPS:
            return _BIN_OPS[op_type](left, right)
        raise ValueError("Unsupported binary operator")

    if isinstance(node, ast.Compare):
        left = _safe_eval(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _safe_eval(comparator, context)
            op_type = type(op)
            if op_type not in _COMPARE_OPS:
                raise ValueError("Unsupported comparison operator")
            if not _COMPARE_OPS[op_type](left, right):
                return False
            left = right
        return True

    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def evaluate(expression: str, context: Dict[str, Any]) -> bool:
    """Safely evaluate a tiny expression language using a restricted AST.

    Any parsing or evaluation error results in ``False`` to mirror the previous
    behaviour where exceptions were swallowed.
    """

    try:
        tree = ast.parse(expression, mode="eval")
        return bool(_safe_eval(tree, context))
    except Exception:
        return False

