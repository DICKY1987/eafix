from __future__ import annotations

"""Constraint repository for dynamic system rules.

This module defines a small SQLite-backed repository that stores
"trading constraints" used to evaluate system health and other
runtime requirements.  Each constraint describes a metric, a
comparison operator and a threshold.  Constraints can be tagged and
queried dynamically based on runtime context (e.g. component name or
constraint type).

The repository replaces static, hard‑coded health checks by providing a
single source of truth that other modules can consult.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import sqlite3
import json


@dataclass
class TradingConstraint:
    """Represents a single constraint record."""

    id: Optional[int]
    name: str
    constraint_type: str
    metric: str
    operator: str
    threshold: float
    tags: Dict[str, Any] | None = None
    severity: str = "WARNING"


class TradingConstraintRepository:
    """SQLite backed repository for trading constraints."""

    def __init__(self, db_path: str = "trading_constraints.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._ensure_schema()

    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS constraints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                constraint_type TEXT NOT NULL,
                metric TEXT NOT NULL,
                operator TEXT NOT NULL,
                threshold REAL NOT NULL,
                tags TEXT,
                severity TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    def add_constraint(self, constraint: TradingConstraint) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO constraints
                (name, constraint_type, metric, operator, threshold, tags, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                constraint.name,
                constraint.constraint_type,
                constraint.metric,
                constraint.operator,
                constraint.threshold,
                json.dumps(constraint.tags or {}),
                constraint.severity,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    # ------------------------------------------------------------------
    def update_constraint(self, constraint: TradingConstraint) -> None:
        if constraint.id is None:
            raise ValueError("Constraint must have id for update")
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE constraints
            SET name=?, constraint_type=?, metric=?, operator=?, threshold=?, tags=?, severity=?
            WHERE id=?
            """,
            (
                constraint.name,
                constraint.constraint_type,
                constraint.metric,
                constraint.operator,
                constraint.threshold,
                json.dumps(constraint.tags or {}),
                constraint.severity,
                constraint.id,
            ),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    def delete_constraint(self, constraint_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM constraints WHERE id=?", (constraint_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    def _row_to_constraint(self, row: sqlite3.Row) -> TradingConstraint:
        tags = json.loads(row[6]) if row[6] else {}
        return TradingConstraint(
            id=row[0],
            name=row[1],
            constraint_type=row[2],
            metric=row[3],
            operator=row[4],
            threshold=row[5],
            tags=tags,
            severity=row[7],
        )

    # ------------------------------------------------------------------
    def list_constraints(self) -> List[TradingConstraint]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name, constraint_type, metric, operator, threshold, tags, severity FROM constraints"
        )
        rows = cur.fetchall()
        return [self._row_to_constraint(row) for row in rows]

    # ------------------------------------------------------------------
    def query_constraints(self, context: Dict[str, Any]) -> List[TradingConstraint]:
        """Return constraints matching the provided context.

        Parameters
        ----------
        context: Dict[str, Any]
            Context values used for filtering.  The special key
            ``constraint_type`` filters by constraint type.  Remaining
            keys must match entries in the ``tags`` dictionary.
        """

        constraint_type = context.get("constraint_type")
        cur = self.conn.cursor()
        if constraint_type:
            cur.execute(
                "SELECT id, name, constraint_type, metric, operator, threshold, tags, severity FROM constraints WHERE constraint_type=?",
                (constraint_type,),
            )
        else:
            cur.execute(
                "SELECT id, name, constraint_type, metric, operator, threshold, tags, severity FROM constraints"
            )
        rows = cur.fetchall()
        result: List[TradingConstraint] = []
        for row in rows:
            constraint = self._row_to_constraint(row)
            tags = constraint.tags or {}
            if all(context.get(k) == v for k, v in tags.items()):
                result.append(constraint)
        return result

    # ------------------------------------------------------------------
    def evaluate(self, metrics: Dict[str, float], context: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate constraints against provided metrics.

        Returns a mapping of constraint name to pass/fail boolean."""

        results: Dict[str, bool] = {}
        for constraint in self.query_constraints(context):
            value = metrics.get(constraint.metric)
            passed = True
            if value is not None:
                if constraint.operator == "lt":
                    passed = value < constraint.threshold
                elif constraint.operator == "le":
                    passed = value <= constraint.threshold
                elif constraint.operator == "gt":
                    passed = value > constraint.threshold
                elif constraint.operator == "ge":
                    passed = value >= constraint.threshold
                elif constraint.operator == "eq":
                    passed = value == constraint.threshold
                elif constraint.operator == "ne":
                    passed = value != constraint.threshold
            results[constraint.name] = passed
        return results

    # ------------------------------------------------------------------
    def close(self) -> None:
        self.conn.close()
