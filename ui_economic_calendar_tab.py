"""Simplified Economic Calendar UI tab scaffold.

This module stitches together placeholder UI components defined in
``ui_components``. The real application would render these sections in a
GUI toolkit, but for testing purposes we merely ensure that each section
is instantiated and accessible.
"""
from ui_components.data_management import DataManagement
from ui_components.anticipation_config import AnticipationConfig
from ui_components.filtering_processing import FilteringProcessing
from ui_components.strategy_ids import StrategyIDs
from ui_components.processing_engine import ProcessingEngine
from ui_components.signal_generation import SignalGeneration
from ui_components.monitoring import Monitoring


class EconomicCalendarTab:
    """Container that exposes all calendar tab sections."""

    def __init__(self) -> None:
        self.data_management = DataManagement()
        self.anticipation_config = AnticipationConfig()
        self.filtering_processing = FilteringProcessing()
        self.strategy_ids = StrategyIDs()
        self.processing_engine = ProcessingEngine()
        self.signal_generation = SignalGeneration()
        self.monitoring = Monitoring()

    def section_names(self):
        """Return the list of available section attribute names."""
        return [
            "data_management",
            "anticipation_config",
            "filtering_processing",
            "strategy_ids",
            "processing_engine",
            "signal_generation",
            "monitoring",
        ]
