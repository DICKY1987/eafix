"""SQLite backed constraint repository."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Tuple


class ConstraintRepository:
    def __init__(self, path: Path):
        self.path = path
        self.conn = sqlite3.connect(path)

    def fetch_all(self) -> Iterable[Tuple[int, str, str]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, expression FROM constraints")
        return cur.fetchall()

