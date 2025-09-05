"""
Theme system for HUEY_P GUI
"""

from .colors import ColorPalette, get_risk_color, get_currency_color, interpolate_color
from .dark_theme import apply_dark_theme, get_widget_colors

__all__ = ['ColorPalette', 'get_risk_color', 'get_currency_color', 'interpolate_color', 
           'apply_dark_theme', 'get_widget_colors']