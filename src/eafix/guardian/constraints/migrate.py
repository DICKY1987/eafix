"""Migration helper to initialise constraint repository."""

from __future__ import annotations

from pathlib import Path
import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS constraints (
    id INTEGER PRIMARY KEY,
    name TEXT,
    expression TEXT
);
"""


def migrate(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

