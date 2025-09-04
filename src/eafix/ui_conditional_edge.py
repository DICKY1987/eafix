"""Tkinter panel that displays conditional probability information.

The real application features a rich GUI with dynamic updates and
performance metrics.  For the purposes of this repository we provide a
minimal yet functional implementation that can be embedded in a Tkinter
application.  The widget exposes a ``set_best_match`` method which can be
used by tests or other modules to update the display.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ConditionalEdgePanel(ttk.Frame):
    """Treeview based panel showing live best match and probability table."""

    columns = ("trigger", "state", "p", "n", "ev", "confidence")

    def __init__(self, master: tk.Misc):
        super().__init__(master)
        self.best_match_var = tk.StringVar(value="-")
        tk.Label(self, text="Live Best Match:").pack(anchor="w")
        tk.Label(self, textvariable=self.best_match_var, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")

        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=5)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def set_best_match(self, text: str) -> None:
        self.best_match_var.set(text)

    def update_table(self, rows: list) -> None:
        """Replace table contents with *rows*.

        Parameters
        ----------
        rows : list of tuple
            Each tuple corresponds to the columns defined in
            :attr:`columns`.
        """
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)


# Convenience for manual testing ------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    panel = ConditionalEdgePanel(root)
    panel.pack(fill="both", expand=True)
    panel.set_best_match("EURUSD burst_10_15")
    panel.update_table([("burst_10_15", "RSI_30_70", 0.55, 120, 5.5, "95%")])
    root.mainloop()
