"""
Dark theme configuration for HUEY_P GUI
"""

try:
    import customtkinter as ctk
    from .colors import ColorPalette
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    # Fallback for when customtkinter is not available

def apply_dark_theme():
    """Apply dark theme configuration to CustomTkinter"""
    
    if not CTK_AVAILABLE:
        return {}
    
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    # Custom color scheme
    dark_theme = {
        "CTk": {
            "fg_color": [ColorPalette.DARK_SURFACE, ColorPalette.DARK_SURFACE]
        },
        "CTkToplevel": {
            "fg_color": [ColorPalette.DARK_SURFACE, ColorPalette.DARK_SURFACE]
        },
        "CTkFrame": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": [ColorPalette.DARK_SURFACE_VARIANT, ColorPalette.DARK_SURFACE_VARIANT],
            "border_color": [ColorPalette.DARK_BORDER, ColorPalette.DARK_BORDER]
        },
        "CTkButton": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": [ColorPalette.INFO, ColorPalette.INFO],
            "hover_color": ["#1E5F8C", "#1E5F8C"],
            "border_color": [ColorPalette.DARK_BORDER, ColorPalette.DARK_BORDER],
            "text_color": [ColorPalette.DARK_TEXT_PRIMARY, ColorPalette.DARK_TEXT_PRIMARY]
        },
        "CTkLabel": {
            "text_color": [ColorPalette.DARK_TEXT_PRIMARY, ColorPalette.DARK_TEXT_PRIMARY]
        },
        "CTkEntry": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": [ColorPalette.DARK_SURFACE, ColorPalette.DARK_SURFACE],
            "border_color": [ColorPalette.DARK_BORDER, ColorPalette.DARK_BORDER],
            "text_color": [ColorPalette.DARK_TEXT_PRIMARY, ColorPalette.DARK_TEXT_PRIMARY]
        },
        "CTkProgressBar": {
            "corner_radius": 4,
            "border_width": 0,
            "fg_color": [ColorPalette.DARK_BORDER, ColorPalette.DARK_BORDER],
            "progress_color": [ColorPalette.SUCCESS, ColorPalette.SUCCESS]
        }
    }
    
    return dark_theme

def get_widget_colors(widget_type: str) -> dict:
    """Get color configuration for specific widget type"""
    theme = apply_dark_theme()
    return theme.get(widget_type, {})

def apply_theme_to_widget(widget, widget_type: str):
    """Apply theme colors directly to a widget"""
    colors = get_widget_colors(widget_type)
    
    if not colors:
        return
        
    # Apply available color properties
    for prop, value in colors.items():
        if hasattr(widget, f'configure'):
            try:
                widget.configure(**{prop: value})
            except:
                pass  # Property might not be available for this widget