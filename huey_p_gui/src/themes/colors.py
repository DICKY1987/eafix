"""
Color palette and color utility functions for HUEY_P GUI
"""

from typing import Dict, Any

class ColorPalette:
    """Central color definitions for trading GUI"""
    
    # Base colors
    SUCCESS = "#1DB954"
    WARNING = "#FFC107" 
    DANGER = "#FF4D4F"
    INFO = "#2D9CDB"
    
    # Dark theme colors
    DARK_SURFACE = "#0F1115"
    DARK_SURFACE_VARIANT = "#1A1D23"
    DARK_TEXT_PRIMARY = "#E6E6E6"
    DARK_TEXT_SECONDARY = "#B3B3B3"
    DARK_BORDER = "#2A2D35"
    
    # Light theme colors
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_SURFACE_VARIANT = "#F5F5F5"
    LIGHT_TEXT_PRIMARY = "#1A1A1A"
    LIGHT_TEXT_SECONDARY = "#666666"
    LIGHT_BORDER = "#E0E0E0"
    
    # Risk level colors
    RISK_SAFE = "#00FF88"
    RISK_CAUTION = "#FFD700"
    RISK_WARNING = "#FF8C00"
    RISK_DANGER = "#FF4444"
    RISK_CRITICAL = "#CC0000"
    
    # Currency colors
    CURRENCY_COLORS = {
        "USD": "#2E8B57",  # Sea green
        "EUR": "#4169E1",  # Royal blue
        "GBP": "#DC143C",  # Crimson
        "JPY": "#FF6347",  # Tomato
        "CHF": "#8B4513",  # Saddle brown
        "AUD": "#FFD700",  # Gold
        "CAD": "#FF1493",  # Deep pink
        "NZD": "#00CED1"   # Dark turquoise
    }

def get_risk_color(risk_ratio: float) -> str:
    """Get color based on risk ratio (0.0 to 1.0+)"""
    if risk_ratio < 0.3:
        return ColorPalette.RISK_SAFE
    elif risk_ratio < 0.6:
        return ColorPalette.RISK_CAUTION
    elif risk_ratio < 0.8:
        return ColorPalette.RISK_WARNING
    elif risk_ratio < 1.0:
        return ColorPalette.RISK_DANGER
    else:
        return ColorPalette.RISK_CRITICAL

def get_currency_color(currency: str) -> str:
    """Get color for specific currency"""
    return ColorPalette.CURRENCY_COLORS.get(currency.upper(), ColorPalette.INFO)

def interpolate_color(color1: str, color2: str, ratio: float) -> str:
    """Interpolate between two hex colors"""
    # Convert hex to RGB
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Interpolate each channel
    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
    
    # Clamp values to 0-255
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    return rgb_to_hex((r, g, b))