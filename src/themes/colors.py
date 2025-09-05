"""Colour palette constants used by UI components.

Only a subset of colours is defined to keep things compact; additional values
can easily be added by the application if required.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Simple namespace for commonly used colour values."""

    DARK_SURFACE: str = "#1e1e1e"
    DARK_SURFACE_VARIANT: str = "#2c2c2c"
    DARK_TEXT_PRIMARY: str = "#ffffff"
    DARK_TEXT_SECONDARY: str = "#bbbbbb"
    DARK_BORDER: str = "#444444"
    INFO: str = "#2196f3"
    SUCCESS: str = "#4caf50"
    WARNING: str = "#ff9800"
    DANGER: str = "#f44336"


__all__ = ["ColorPalette"]
