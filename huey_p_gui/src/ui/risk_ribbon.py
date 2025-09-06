"""
Risk Ribbon - Always visible risk monitoring and emergency controls
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta
import threading
import time
import sys
import os

# Add path for core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.event_bus import event_bus
from core.state_manager import state_manager, RiskMetrics, ConnectivityStatus
from themes.colors import ColorPalette, get_risk_color, interpolate_color
from ui.modern_widgets import (
    ModernFrame,
    ModernButton,
    ModernLabel,
    RiskMeter,
    CTK_AVAILABLE,
)

class ConnectionIndicator:
    """Visual indicator for DDE connection status"""
    
    def __init__(self, master):
        self.master = master
        self.frame = ModernFrame(master)
        self.setup_ui()
        self.update_timer = None
        self.start_monitoring()
    
    def setup_ui(self):
        """Setup connection indicator UI"""
        # Status indicator (colored circle)
        self.status_canvas = tk.Canvas(
            self.frame.widget, 
            width=20, 
            height=20, 
            bg=ColorPalette.DARK_SURFACE_VARIANT,
            highlightthickness=0
        )
        self.status_canvas.pack(side=tk.LEFT, padx=(5, 2))
        
        # Status label
        self.status_label = ModernLabel(
            self.frame.widget,
            text="Disconnected"
        )
        self.status_label.pack(side=tk.LEFT, padx=2)
        
        # Symbol count
        self.symbol_label = ModernLabel(
            self.frame.widget,
            text="0 symbols"
        )
        self.symbol_label.pack(side=tk.LEFT, padx=(10, 5))
        
        # Draw initial disconnected indicator
        self.draw_status_indicator(False)
    
    def draw_status_indicator(self, connected: bool):
        """Draw colored status indicator"""
        self.status_canvas.delete("all")
        color = ColorPalette.SUCCESS if connected else ColorPalette.DANGER
        
        # Draw circle
        self.status_canvas.create_oval(
            4, 4, 16, 16,
            fill=color,
            outline=color
        )
    
    def start_monitoring(self):
        """Start monitoring connection status"""
        self.update_connection_status()
    
    def update_connection_status(self):
        """Update connection status from state manager"""
        try:
            conn_status = state_manager.get_connectivity_status()
            
            # Update visual indicator
            self.draw_status_indicator(conn_status.dde_connected)
            
            # Update status text
            status_text = "Connected" if conn_status.dde_connected else "Disconnected"
            if conn_status.connection_quality != "unknown":
                status_text += f" ({conn_status.connection_quality})"
            
            # Update symbol count and determine color coding
            symbol_text = (
                f"{conn_status.symbol_count} symbol"
                f"{'s' if conn_status.symbol_count != 1 else ''}"
            )

            if conn_status.dde_connected:
                if conn_status.connection_quality == "excellent":
                    color = ColorPalette.SUCCESS
                elif conn_status.connection_quality == "good":
                    color = ColorPalette.INFO
                else:
                    color = ColorPalette.WARNING
            else:
                color = ColorPalette.DANGER

            # Apply text updates with proper color tokens
            self.status_label.configure(text=status_text)
            self.symbol_label.configure(text=symbol_text)
            try:
                if CTK_AVAILABLE:
                    self.status_label.configure(text_color=color)
                    self.symbol_label.configure(text_color=color)
                else:
                    self.status_label.configure(foreground=color)
                    self.symbol_label.configure(foreground=color)
            except Exception:
                pass  # Fallback silently if widget doesn't support color update
            
            # Schedule next update
            if self.update_timer:
                self.master.after_cancel(self.update_timer)
            self.update_timer = self.master.after(1000, self.update_connection_status)
            
        except Exception as e:
            print(f"Error updating connection status: {e}")
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

class EmergencyControls:
    """Emergency trading controls"""
    
    def __init__(self, master):
        self.master = master
        self.frame = ModernFrame(master)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup emergency controls"""
        # Emergency stop button
        self.stop_button = ModernButton(
            self.frame.widget,
            text="EMERGENCY STOP",
            command=self.emergency_stop
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Pause trading button
        self.pause_button = ModernButton(
            self.frame.widget,
            text="PAUSE",
            command=self.pause_trading
        )
        self.pause_button.pack(side=tk.LEFT, padx=2)
        
        # Resume button (initially disabled)
        self.resume_button = ModernButton(
            self.frame.widget,
            text="RESUME",
            command=self.resume_trading
        )
        self.resume_button.pack(side=tk.LEFT, padx=2)
    
    def emergency_stop(self):
        """Execute emergency stop"""
        try:
            # Publish emergency stop event
            event_bus.publish(
                "emergency_stop",
                {"action": "stop_all_trading", "timestamp": datetime.now()},
                "risk_ribbon"
            )
            print("Emergency stop activated!")
        except Exception as e:
            print(f"Error during emergency stop: {e}")
    
    def pause_trading(self):
        """Pause trading"""
        try:
            event_bus.publish(
                "trading_control",
                {"action": "pause", "timestamp": datetime.now()},
                "risk_ribbon"
            )
            print("Trading paused")
        except Exception as e:
            print(f"Error pausing trading: {e}")
    
    def resume_trading(self):
        """Resume trading"""
        try:
            event_bus.publish(
                "trading_control", 
                {"action": "resume", "timestamp": datetime.now()},
                "risk_ribbon"
            )
            print("Trading resumed")
        except Exception as e:
            print(f"Error resuming trading: {e}")
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

class RiskRibbon:
    """Main risk ribbon component"""
    
    def __init__(self, master):
        self.master = master
        self.main_frame = ModernFrame(master)
        self.setup_ui()
        self.start_updates()
    
    def setup_ui(self):
        """Setup risk ribbon UI"""
        # Connection status (left side)
        self.connection_indicator = ConnectionIndicator(self.main_frame.widget)
        self.connection_indicator.pack(side=tk.LEFT, padx=10)
        
        # Risk meters (center)
        self.risk_frame = ModernFrame(self.main_frame.widget)
        self.risk_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        
        # Daily drawdown meter
        self.dd_meter = RiskMeter(
            self.risk_frame.widget,
            "Daily DD"
        )
        self.dd_meter.pack(side=tk.LEFT, padx=5)
        
        # Portfolio risk meter
        self.risk_meter = RiskMeter(
            self.risk_frame.widget,
            "Portfolio"
        )
        self.risk_meter.pack(side=tk.LEFT, padx=5)
        
        # Session cap meter
        self.session_meter = RiskMeter(
            self.risk_frame.widget,
            "Session"
        )
        self.session_meter.pack(side=tk.LEFT, padx=5)
        
        # Emergency controls (right side)
        self.emergency_controls = EmergencyControls(self.main_frame.widget)
        self.emergency_controls.pack(side=tk.RIGHT, padx=10)
        
        # Trading status label
        self.status_label = ModernLabel(
            self.main_frame.widget,
            text="Trading Status: Allowed"
        )
        self.status_label.pack(side=tk.RIGHT, padx=(20, 10))
    
    def start_updates(self):
        """Start periodic risk updates"""
        self.update_risk_metrics()
    
    def update_risk_metrics(self):
        """Update all risk metrics"""
        try:
            risk_metrics = state_manager.get_risk_metrics()
            
            # Update daily drawdown meter
            dd_ratio = abs(risk_metrics.daily_drawdown) / risk_metrics.daily_limit * 100
            self.dd_meter.update_value(dd_ratio, 100)
            
            # Update portfolio risk meter
            self.risk_meter.update_value(risk_metrics.portfolio_risk * 100, 100)
            
            # Update session cap meter
            session_ratio = risk_metrics.session_cap_used / risk_metrics.session_cap_limit * 100
            self.session_meter.update_value(session_ratio, 100)
            
            # Update trading status
            is_allowed, reason = state_manager.is_action_allowed()
            status_text = f"Trading: {'Allowed' if is_allowed else 'BLOCKED'}"
            if not is_allowed:
                status_text += f" ({reason})"
            
            self.status_label.configure(text=status_text)
            
            # Color code the status
            if is_allowed:
                color = ColorPalette.SUCCESS
            else:
                color = ColorPalette.DANGER
            
            # Schedule next update
            self.master.after(2000, self.update_risk_metrics)
            
        except Exception as e:
            print(f"Error updating risk metrics: {e}")
            # Retry after longer delay on error
            self.master.after(5000, self.update_risk_metrics)
    
    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.main_frame.grid(**kwargs)
