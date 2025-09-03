import tkinter as tk
import random
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "indicator_tab", Path(__file__).resolve().parent.parent / "tabs" / "indicator_tab.py"
)
indicator_module = importlib.util.module_from_spec(spec)
import sys
sys.modules["indicator_tab"] = indicator_module
spec.loader.exec_module(indicator_module)
IndicatorsTab = indicator_module.IndicatorsTab


def test_add_indicator_and_refresh(monkeypatch):
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tkinter display not available")
    tab = IndicatorsTab(root, None)
    tab.indicator_var.set("SMA")
    tab.period_var.set(3)
    tab.add_indicator()
    name = next(iter(tab.indicators))
    # Controlled price history and randomness
    tab.price_history = [1.0, 2.0, 3.0, 4.0]
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    tab.refresh_data()
    item = tab.tree.item(name, "values")
    assert float(item[2]) == pytest.approx((4.0 + 4.0 + 3.0) / 3)
    root.destroy()


def test_overlay_toggle():
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tkinter display not available")
    tab = IndicatorsTab(root, None)
    tab.indicator_var.set("EMA")
    tab.period_var.set(3)
    tab.add_indicator()
    name = next(iter(tab.indicators))
    tab.tree.selection_set(name)
    tab.toggle_selected_overlay()
    assert tab.indicators[name].overlay is True
    tab.toggle_selected_overlay()
    assert tab.indicators[name].overlay is False
    root.destroy()
