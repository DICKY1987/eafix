import pytest

try:
    import tkinter as tk
except Exception:  # pragma: no cover - tkinter not installed
    tk = None

from eafix.ui_indicator_toggle import IndicatorTogglePanel


@pytest.mark.skipif(tk is None, reason="Tkinter not installed")
def test_indicator_toggle_states():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter cannot open a display")
    root.withdraw()
    panel = IndicatorTogglePanel(root)
    panel.add_indicator("RSI")
    panel.add_indicator("MACD", enabled=False)

    with pytest.raises(ValueError):
        panel.add_indicator("RSI")

    assert panel.is_enabled("RSI") is True
    assert panel.is_enabled("MACD") is False

    panel.set_enabled("MACD", True)
    assert panel.is_enabled("MACD") is True

    with pytest.raises(KeyError):
        panel.is_enabled("UNKNOWN")

    with pytest.raises(KeyError):
        panel.set_enabled("UNKNOWN", True)

    root.destroy()
