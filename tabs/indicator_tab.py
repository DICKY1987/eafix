"""Indicator management and display tab for technical indicators."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class IndicatorData:
    """Container for indicator configuration and state."""

    name: str
    type: str
    period: int
    overlay: bool = False
    value: float | None = None
    _prev_ema: float | None = None  # internal state for EMA

    def update(self, prices: List[float]) -> None:
        """Update indicator value using provided price history."""
        if self.type == "SMA":
            if len(prices) >= self.period:
                self.value = sum(prices[-self.period:]) / self.period
        elif self.type == "EMA":
            if len(prices) >= self.period:
                if self._prev_ema is None:
                    self.value = sum(prices[-self.period:]) / self.period
                else:
                    multiplier = 2 / (self.period + 1)
                    self.value = (prices[-1] - self._prev_ema) * multiplier + self._prev_ema
                self._prev_ema = self.value
        elif self.type == "RSI":
            if len(prices) >= self.period + 1:
                gains: float = 0.0
                losses: float = 0.0
                for i in range(-self.period, 0):
                    change = prices[i] - prices[i - 1]
                    if change >= 0:
                        gains += change
                    else:
                        losses -= change
                avg_gain = gains / self.period
                avg_loss = losses / self.period
                if avg_loss == 0:
                    self.value = 100.0
                else:
                    rs = avg_gain / avg_loss
                    self.value = 100 - (100 / (1 + rs))


class IndicatorsTab:
    """Tab for displaying and managing technical indicators."""

    def __init__(self, parent: ttk.Notebook, app_controller) -> None:
        self.parent = parent
        self.app_controller = app_controller
        self.frame = ttk.Frame(parent)
        self.indicators: Dict[str, IndicatorData] = {}
        self.price_history: List[float] = [100.0]
        self.auto_refresh = False
        self.refresh_job: str | None = None

        # UI variables
        self.indicator_var = tk.StringVar()
        self.period_var = tk.IntVar(value=14)
        self.refresh_interval = tk.IntVar(value=5)

        self._setup_ui()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self) -> None:
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Controls
        control_frame = ttk.LabelFrame(main_container, text="Controls", padding=10)
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="Indicator:").pack(side=tk.LEFT)
        combo = ttk.Combobox(
            control_frame,
            textvariable=self.indicator_var,
            values=["SMA", "EMA", "RSI"],
            state="readonly",
            width=8,
        )
        combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Period:").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Entry(control_frame, textvariable=self.period_var, width=5).pack(side=tk.LEFT)

        ttk.Button(control_frame, text="Add", command=self.add_indicator).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Refresh (s):").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Entry(control_frame, textvariable=self.refresh_interval, width=5).pack(side=tk.LEFT)

        self.auto_btn = ttk.Button(control_frame, text="Start", command=self.toggle_auto_refresh)
        self.auto_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Toggle Overlay", command=self.toggle_selected_overlay).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Remove", command=self.remove_selected).pack(side=tk.LEFT)

        # Indicator display
        columns = ("Name", "Type", "Value", "Overlay")
        self.tree = ttk.Treeview(main_container, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # ------------------------------------------------------------------ indicator management
    def add_indicator(self) -> None:
        indicator_type = self.indicator_var.get()
        period = self.period_var.get()
        if not indicator_type:
            return
        base_name = f"{indicator_type}_{period}"
        name = base_name
        counter = 1
        while name in self.indicators:
            name = f"{base_name}_{counter}"
            counter += 1
        self.indicators[name] = IndicatorData(name, indicator_type, period)
        self.tree.insert("", "end", iid=name, values=(name, indicator_type, "-", "Off"))

    def remove_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        self.tree.delete(item)
        self.indicators.pop(item, None)

    def toggle_selected_overlay(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        data = self.indicators.get(item)
        if not data:
            return
        data.overlay = not data.overlay
        overlay_text = "On" if data.overlay else "Off"
        vals = list(self.tree.item(item, "values"))
        vals[3] = overlay_text
        self.tree.item(item, values=vals)

    # ------------------------------------------------------------------ refreshing
    def toggle_auto_refresh(self) -> None:
        if self.auto_refresh:
            self.auto_refresh = False
            self.auto_btn.config(text="Start")
            if self.refresh_job is not None:
                self.frame.after_cancel(self.refresh_job)
                self.refresh_job = None
        else:
            self.auto_refresh = True
            self.auto_btn.config(text="Stop")
            self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        if self.auto_refresh:
            self.refresh_data()
            interval = max(1, self.refresh_interval.get()) * 1000
            self.refresh_job = self.frame.after(interval, self._schedule_refresh)

    def refresh_data(self) -> None:
        """Generate a new price and update all indicators."""
        last_price = self.price_history[-1]
        new_price = last_price + random.uniform(-0.5, 0.5)
        self.price_history.append(round(new_price, 5))

        for name, indicator in self.indicators.items():
            indicator.update(self.price_history)
            value_text = "-" if indicator.value is None else f"{indicator.value:.5f}"
            overlay_text = "On" if indicator.overlay else "Off"
            self.tree.item(name, values=(name, indicator.type, value_text, overlay_text))
