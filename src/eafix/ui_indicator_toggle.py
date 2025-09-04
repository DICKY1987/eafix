"""Tkinter panel for toggling indicator signals."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict


class IndicatorTogglePanel(ttk.Frame):
    """Panel providing checkbuttons to enable/disable indicator signals.

    The widget manages a mapping of indicator names to :class:`~tkinter.BooleanVar`
    instances.  Each indicator appears as a checkbutton that allows the user to
    quickly enable or disable whether signals from that indicator should be
    forwarded.  The panel itself does not implement any signalling logic – it
    merely tracks the on/off state for consumers to query.
    """

    def __init__(self, master: tk.Misc):
        super().__init__(master)
        self._vars: Dict[str, tk.BooleanVar] = {}
        self.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    def add_indicator(self, name: str, *, enabled: bool = True) -> None:
        """Add an indicator toggle to the panel.

        Parameters
        ----------
        name:
            Name of the indicator.
        enabled:
            Whether the indicator should start in the enabled state.

        Raises
        ------
        ValueError
            If *name* already exists in the panel.
        """
        if name in self._vars:
            raise ValueError(f"Indicator '{name}' already present")
        var = tk.BooleanVar(value=enabled)
        cb = ttk.Checkbutton(self, text=name, variable=var)
        cb.pack(anchor="w")
        self._vars[name] = var

    def is_enabled(self, name: str) -> bool:
        """Return ``True`` if the indicator is currently enabled."""
        if name not in self._vars:
            raise KeyError(f"Indicator '{name}' not present")
        return bool(self._vars[name].get())

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Programmatically set the enabled state of *name* indicator.

        Raises
        ------
        KeyError
            If *name* does not exist in the panel.
        """
        if name not in self._vars:
            raise KeyError(f"Indicator '{name}' not present")
        self._vars[name].set(enabled)


# Convenience for manual testing ------------------------------------------------
if __name__ == "__main__":  # pragma: no cover - manual testing
    root = tk.Tk()
    panel = IndicatorTogglePanel(root)
    panel.pack(fill="both", expand=True)
    panel.add_indicator("RSI")
    panel.add_indicator("MACD", enabled=False)
    root.mainloop()
