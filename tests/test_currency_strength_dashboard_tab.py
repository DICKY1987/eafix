import tkinter as tk
import pytest
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "currency_strength_dashboard",
    Path(__file__).resolve().parent.parent / "tabs" / "currency_strength_dashboard.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CurrencyStrengthDashboardTab = module.CurrencyStrengthDashboardTab


def test_strength_tab_refresh_populates_tree():
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tkinter display not available")

    frame = tk.Frame(root)
    frame.pack()
    tab = CurrencyStrengthDashboardTab(frame)
    tab.refresh()
    assert tab.tree.get_children()  # rows populated
    root.destroy()
