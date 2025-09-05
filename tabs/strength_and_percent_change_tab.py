"""Comprehensive Strength & Percent Change tab implementation.

This module is largely based on the design brief from the project description
and implements oscillator calculations (RSI, Stochastic, Z-Score) together with
basic UI plumbing.  Many of the visual aspects are intentionally simplified so
that the code can run in environments without the original dependencies.
"""

from __future__ import annotations

import math
import threading
from datetime import datetime
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import customtkinter as ctk  # type: ignore
    import tkinter as tk
except Exception:  # pragma: no cover - fallback
    import tkinter as tk  # type: ignore
    class _Dummy(tk.Frame):
        def __init__(self, *a, **kw):  # pragma: no cover - trivial
            super().__init__(*a, **kw)
    ctk = type(
        "ctk",
        (),
        {
            "CTk": tk.Tk,
            "CTkFrame": tk.Frame,
            "CTkLabel": tk.Label,
            "CTkEntry": tk.Entry,
            "CTkButton": tk.Button,
            "CTkSlider": tk.Scale,
            "CTkFont": lambda *a, **k: None,
            "CTkToplevel": tk.Toplevel,
        },
    )

from core.event_bus import event_bus
from ui.toast_manager import show_info, show_warning
from themes.colors import ColorPalette


# ---------------------------------------------------------------------------
# Placeholder widgets -------------------------------------------------------


class AdvancedTableWidget(ctk.CTkFrame):  # pragma: no cover - UI helper
    def __init__(self, master, title: str, columns: List[str], show_sparklines: bool = False):
        super().__init__(master)
        self.columns = columns

    def update_rows(self, rows: List[Dict[str, Any]]) -> None:
        pass


class HeatmapWidget(ctk.CTkFrame):  # pragma: no cover - UI helper
    def __init__(self, master, currencies: List[str], timeframes: List[str]):
        super().__init__(master)

    def update_data(self, data: Dict[str, Dict[str, float]]) -> None:
        pass


class OscillatorDrilldownWindow(ctk.CTkToplevel):  # pragma: no cover - UI helper
    def __init__(self, master, currency: str, oscillator_type: str):
        super().__init__(master)
        self.title(f"{oscillator_type} - {currency}")


# ---------------------------------------------------------------------------
# Oscillator calculation helpers


class OscillatorCalculator:
    """Collection of oscillator helper methods."""

    @staticmethod
    def calculate_rsi(values: List[float], period: int) -> float:
        if len(values) < period + 1:
            return 50.0
        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, len(values)):
            change = values[i] - values[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_stochastic(values: List[float], period: int) -> float:
        if len(values) < period:
            return 50.0
        recent = values[-period:]
        high = max(recent)
        low = min(recent)
        if high == low:
            return 50.0
        return ((values[-1] - low) / (high - low)) * 100

    @staticmethod
    def calculate_zscore(values: List[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        recent = values[-period:]
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        std_dev = math.sqrt(variance)
        if std_dev == 0:
            return 0.0
        return (values[-1] - mean) / std_dev


# ---------------------------------------------------------------------------
# Main tab implementation


class StrengthAndPercentChangeTab(ctk.CTkFrame):  # pragma: no cover - UI heavy
    """Main Strength & % Change Tab with enhanced features."""

    def __init__(self, master, **kwargs):
        default_kwargs = {"fg_color": ColorPalette.DARK_SURFACE, "corner_radius": 0}
        default_kwargs.update(kwargs)
        super().__init__(master, **default_kwargs)

        self.timeframes = ["15m", "1h", "4h", "8h", "12h", "24h"]
        self.currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]

        self.pair_data: Dict[str, Dict[str, float]] = {}
        self.currency_strength_data: Dict[str, Dict[str, float]] = {}
        self.update_lock = threading.Lock()
        self.last_update = datetime.now()
        self.update_interval = 1.0

        self.setup_ui()
        self.setup_event_handlers()
        self.start_update_loop()

    # ------------------------------------------------------------------ setup
    def setup_ui(self) -> None:  # pragma: no cover - simplified UI
        main_paned = ctk.CTkFrame(self, fg_color="transparent")
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)
        tables_frame = ctk.CTkFrame(main_paned, fg_color="transparent")
        tables_frame.pack(fill="both", expand=True)
        pair_columns = ["Pair"] + self.timeframes
        self.pair_table = AdvancedTableWidget(tables_frame, title="Currency Pair % Changes", columns=pair_columns, show_sparklines=True)
        self.pair_table.pack(side="left", expand=True, fill="both")
        strength_columns = ["Currency"] + self.timeframes
        self.strength_table = AdvancedTableWidget(tables_frame, title="Currency Strength", columns=strength_columns, show_sparklines=True)
        self.strength_table.pack(side="left", expand=True, fill="both")
        self.strength_table.bind = lambda *a, **k: None  # type: ignore - placeholder
        bottom_frame = ctk.CTkFrame(main_paned, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))
        button_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        refresh_button = ctk.CTkButton(button_frame, text="Refresh", command=self.force_refresh)
        refresh_button.pack(side="left")
        export_button = ctk.CTkButton(button_frame, text="Export", command=self.export_data)
        export_button.pack(side="left")
        settings_button = ctk.CTkButton(button_frame, text="Settings", command=self.show_settings)
        settings_button.pack(side="left")
        self.frequency_slider = ctk.CTkSlider(button_frame, from_=0.5, to=5.0)
        self.frequency_slider.pack(side="right")
        self.frequency_slider.set(1.0)
        self.frequency_label = ctk.CTkLabel(button_frame, text="1.0s")
        self.frequency_label.pack(side="right")
        self.frequency_slider.configure(command=self.on_frequency_changed)
        heatmap_frame = ctk.CTkFrame(bottom_frame)
        heatmap_frame.pack(fill="x")
        self.heatmap_content = ctk.CTkFrame(heatmap_frame)
        self.heatmap_widget = HeatmapWidget(self.heatmap_content, currencies=self.currencies, timeframes=self.timeframes)
        self.heatmap_widget.pack(fill="both", expand=True, padx=10, pady=10)
        self.heatmap_visible = False
        self.heatmap_toggle = ctk.CTkButton(heatmap_frame, text="Show Heatmap", command=self.toggle_heatmap)
        self.heatmap_toggle.pack()
        self.chart_canvas = tk.Canvas(self, height=150)
        self.chart_canvas.pack(fill="x", padx=10, pady=10)
        self.signal_label = ctk.CTkLabel(self, text="Signal:")
        self.signal_label.pack()
        self.current_value_label = ctk.CTkLabel(self, text="Current Value:")
        self.current_value_label.pack()
        self.ob_entry = ctk.CTkEntry(self)
        self.os_entry = ctk.CTkEntry(self)
        self.oscillator_type = "StrengthRSI"

    def setup_event_handlers(self) -> None:
        event_bus.subscribe("market_data_update", self._handle_market_data_update)
        event_bus.subscribe("currency_strength_update", self._handle_currency_strength_update)

    def start_update_loop(self) -> None:
        self.update_display()
        self.after(int(self.update_interval * 1000), self.start_update_loop)

    # ------------------------------------------------------------------ event handlers
    def _handle_market_data_update(self, event):
        data = event.data
        with self.update_lock:
            if 'symbols' in data:
                self.pair_data.update(data['symbols'])
            if 'currency_strength' in data:
                self.currency_strength_data.update(data['currency_strength'])

    def _handle_currency_strength_update(self, event):
        data = event.data
        with self.update_lock:
            self.currency_strength_data.update(data)

    # ------------------------------------------------------------------ UI callbacks
    def on_frequency_changed(self, value):
        self.update_interval = float(value)
        self.frequency_label.configure(text=f"{value:.1f}s")

    def toggle_heatmap(self) -> None:
        if self.heatmap_visible:
            self.heatmap_content.pack_forget()
            self.heatmap_visible = False
            self.heatmap_toggle.configure(text="Show Heatmap")
        else:
            self.heatmap_content.pack(fill="x", padx=10, pady=10)
            self.heatmap_visible = True
            self.heatmap_toggle.configure(text="Hide Heatmap")
            self.update_heatmap()

    def update_heatmap(self) -> None:
        if self.heatmap_visible and self.currency_strength_data:
            self.heatmap_widget.update_data(self.currency_strength_data)

    def force_refresh(self) -> None:
        event_bus.publish("force_data_refresh", {"timestamp": datetime.now().isoformat()}, "strength_tab")
        show_info("Data refresh requested")

    def export_data(self) -> None:
        show_info("Export not implemented in demo")

    def show_settings(self) -> None:
        show_info("Settings dialog not implemented in demo")

    # ------------------------------------------------------------------ update display
    def update_display(self) -> None:
        current_time = datetime.now()
        if (current_time - self.last_update).total_seconds() < self.update_interval:
            return
        try:
            with self.update_lock:
                if self.pair_data:
                    pair_rows: List[Dict[str, Any]] = []
                    for pair, data in self.pair_data.items():
                        row = {"name": pair}
                        for tf in self.timeframes:
                            row[tf] = data.get(tf, 0.0)
                        pair_rows.append(row)
                    self.pair_table.update_rows(pair_rows)
                if self.currency_strength_data:
                    strength_rows: List[Dict[str, Any]] = []
                    for currency, data in self.currency_strength_data.items():
                        row = {"name": currency}
                        for tf in self.timeframes:
                            row[tf] = data.get(tf, 0.0)
                        strength_rows.append(row)
                    self.strength_table.update_rows(strength_rows)
                if self.heatmap_visible:
                    self.update_heatmap()
            self.last_update = current_time
        except Exception as exc:  # pragma: no cover
            print(f"Error updating strength tab display: {exc}")


# ---------------------------------------------------------------------------
# Integration helper


def integrate_strength_tab(notebook_widget) -> StrengthAndPercentChangeTab:  # pragma: no cover - UI helper
    strength_tab = StrengthAndPercentChangeTab(notebook_widget)
    if hasattr(notebook_widget, 'add'):
        notebook_widget.add("\U0001F4AA Strength & Changes")
        tab_frame = notebook_widget.tab("\U0001F4AA Strength & Changes")
        strength_tab.pack(fill="both", expand=True)
    return strength_tab


__all__ = ["StrengthAndPercentChangeTab", "integrate_strength_tab", "OscillatorCalculator"]
