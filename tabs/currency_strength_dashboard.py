"""Currency Strength Dashboard tab for visualizing relative currency performance."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk
from typing import Dict

from pathlib import Path
import sys

# Ensure project root for imports
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from eafix.currency_strength import calc_currency_strength
from eafix.strength_feed import StrengthFeed


class CurrencyStrengthDashboardTab:
    """Display current currency strength readings with basic analytics."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.feed = StrengthFeed(window=200)
        self.tree: ttk.Treeview | None = None
        self._setup_ui()

    # ------------------------------------------------------------------ UI setup
    def _setup_ui(self) -> None:
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(
            container,
            text="Currency Strength Dashboard",
            font=("Arial", 16, "bold"),
        ).pack(pady=(0, 10))

        control = ttk.Frame(container)
        control.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(control, text="Refresh", command=self.refresh).pack(side=tk.LEFT)

        columns = ("Currency", "Strength", "Z-Score")
        tree = ttk.Treeview(container, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True)
        self.tree = tree

    # ------------------------------------------------------------------ data handling
    def refresh(self) -> None:
        """Simulate strength update using random pair changes."""
        pairs = [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
            "USDCHF",
            "NZDUSD",
        ]
        pair_changes: Dict[str, float] = {p: random.uniform(-0.5, 0.5) for p in pairs}
        strengths = calc_currency_strength(pair_changes)
        self.feed.update(strengths)

        for ccy, val in strengths.items():
            z = self.feed.zscore(ccy)
            row_id = ccy
            values = (ccy, f"{val:.2f}", f"{z:.2f}")
            if self.tree.exists(row_id):
                self.tree.item(row_id, values=values)
            else:
                self.tree.insert("", tk.END, iid=row_id, values=values)
