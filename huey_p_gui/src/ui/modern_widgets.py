"""
Modern widget implementations that work with or without CustomTkinter
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any
import sys
import os

# Add path for themes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from themes.colors import ColorPalette, get_risk_color

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

class ModernFrame:
    """Modern frame widget that adapts to available libraries"""
    
    def __init__(self, master, **kwargs):
        if CTK_AVAILABLE:
            self.widget = ctk.CTkFrame(master, **kwargs)
        else:
            # Fallback to tkinter
            self.widget = ttk.Frame(master, **kwargs)
            self.widget.configure(style="Modern.TFrame")
    
    def pack(self, **kwargs):
        self.widget.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.widget.grid(**kwargs)
    
    def place(self, **kwargs):
        self.widget.place(**kwargs)
    
    def configure(self, **kwargs):
        self.widget.configure(**kwargs)

class ModernButton:
    """Modern button widget that adapts to available libraries"""
    
    def __init__(self, master, text: str = "", command: Optional[Callable] = None, **kwargs):
        if CTK_AVAILABLE:
            self.widget = ctk.CTkButton(master, text=text, command=command, **kwargs)
        else:
            # Fallback to tkinter
            self.widget = ttk.Button(master, text=text, command=command, **kwargs)
            self.widget.configure(style="Modern.TButton")
    
    def pack(self, **kwargs):
        self.widget.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.widget.grid(**kwargs)
    
    def place(self, **kwargs):
        self.widget.place(**kwargs)
    
    def configure(self, **kwargs):
        self.widget.configure(**kwargs)

class ModernLabel:
    """Modern label widget that adapts to available libraries"""
    
    def __init__(self, master, text: str = "", **kwargs):
        if CTK_AVAILABLE:
            self.widget = ctk.CTkLabel(master, text=text, **kwargs)
        else:
            # Fallback to tkinter
            self.widget = ttk.Label(master, text=text, **kwargs)
            self.widget.configure(style="Modern.TLabel")
    
    def pack(self, **kwargs):
        self.widget.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.widget.grid(**kwargs)
    
    def place(self, **kwargs):
        self.widget.place(**kwargs)
    
    def configure(self, **kwargs):
        self.widget.configure(**kwargs)

class ModernProgressBar:
    """Modern progress bar widget that adapts to available libraries"""
    
    def __init__(self, master, **kwargs):
        if CTK_AVAILABLE:
            self.widget = ctk.CTkProgressBar(master, **kwargs)
        else:
            # Fallback to tkinter - filter out unsupported options
            tkinter_kwargs = {}
            for key, value in kwargs.items():
                if key in ['length', 'orient', 'mode', 'maximum', 'value', 'variable', 'phase']:
                    tkinter_kwargs[key] = value
            
            self.widget = ttk.Progressbar(master, **tkinter_kwargs)
            self.widget.configure(style="Modern.Horizontal.TProgressbar")
    
    def pack(self, **kwargs):
        self.widget.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.widget.grid(**kwargs)
    
    def place(self, **kwargs):
        self.widget.place(**kwargs)
    
    def configure(self, **kwargs):
        self.widget.configure(**kwargs)
    
    def set(self, value: float):
        """Set progress bar value (0.0 to 1.0)"""
        if CTK_AVAILABLE:
            self.widget.set(value)
        else:
            self.widget['value'] = value * 100

class RiskMeter:
    """Risk meter component with progress bar and value display"""
    
    def __init__(self, master, title: str, **kwargs):
        self.master = master
        self.title = title
        self.current_value = 0.0
        self.max_value = 100.0
        self.warning_threshold = 70.0
        self.danger_threshold = 90.0
        
        # Create main frame
        self.frame = ModernFrame(master, **kwargs)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup meter UI components"""
        
        # Title label
        self.title_label = ModernLabel(
            self.frame.widget,
            text=self.title
        )
        self.title_label.pack(pady=(5, 2))
        
        # Progress bar
        self.progress_bar = ModernProgressBar(
            self.frame.widget,
            length=150
        )
        self.progress_bar.pack(pady=2)
        
        # Value label
        self.value_label = ModernLabel(
            self.frame.widget,
            text="0.0%"
        )
        self.value_label.pack(pady=(2, 5))
    
    def update_value(self, value: float, max_value: float = None):
        """Update meter value and appearance"""
        self.current_value = value
        if max_value is not None:
            self.max_value = max_value
        
        # Calculate ratio and update progress bar
        ratio = min(value / self.max_value, 1.0) if self.max_value > 0 else 0.0
        self.progress_bar.set(ratio)
        
        # Update value label
        self.value_label.configure(text=f"{value:.1f}%")
        
        # Update colors based on risk level
        risk_color = get_risk_color(ratio)
        try:
            if CTK_AVAILABLE:
                self.progress_bar.configure(progress_color=risk_color)
                self.value_label.configure(text_color=risk_color)
        except:
            pass  # Color setting might fail on fallback widgets
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

def setup_modern_styles():
    """Setup modern styles for fallback ttk widgets"""
    style = ttk.Style()
    
    # Configure modern frame style
    style.configure(
        "Modern.TFrame",
        background=ColorPalette.DARK_SURFACE_VARIANT,
        borderwidth=1,
        relief="solid"
    )
    
    # Configure modern button style
    style.configure(
        "Modern.TButton",
        background=ColorPalette.INFO,
        foreground=ColorPalette.DARK_TEXT_PRIMARY,
        borderwidth=1,
        focuscolor="none"
    )
    
    # Configure modern label style
    style.configure(
        "Modern.TLabel",
        background=ColorPalette.DARK_SURFACE_VARIANT,
        foreground=ColorPalette.DARK_TEXT_PRIMARY
    )
    
    # Configure modern progressbar style
    style.configure(
        "Modern.Horizontal.TProgressbar",
        background=ColorPalette.DARK_BORDER,
        troughcolor=ColorPalette.DARK_BORDER,
        borderwidth=0,
        lightcolor=ColorPalette.SUCCESS,
        darkcolor=ColorPalette.SUCCESS
    )