"""
HUEY_P Modern GUI Application
Integrates with existing trading system
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from datetime import datetime, timedelta
import threading
import time

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our modern components
from core.event_bus import event_bus
from core.state_manager import state_manager
from themes.dark_theme import apply_dark_theme
from themes.colors import ColorPalette
from ui.modern_widgets import setup_modern_styles, ModernFrame, ModernLabel
from ui.risk_ribbon import RiskRibbon

class HueyPModernApp:
    """Main HUEY_P Modern GUI Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HUEY_P Trading System - Modern GUI")
        self.root.geometry("1200x800")
        self.root.configure(bg=ColorPalette.DARK_SURFACE)
        
        # Apply modern styling
        self.setup_styling()
        
        # Setup main UI
        self.setup_ui()
        
        # Start background services
        self.start_services()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styling(self):
        """Setup modern styling for the application"""
        try:
            # Apply dark theme if CustomTkinter is available
            apply_dark_theme()
        except:
            pass
        
        # Setup fallback TTK styles
        setup_modern_styles()
        
        # Configure root window
        style = ttk.Style()
        style.theme_use('clam')  # Modern base theme
    
    def setup_ui(self):
        """Setup main user interface"""
        
        # Main container
        self.main_container = ModernFrame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Risk ribbon (top)
        self.risk_ribbon = RiskRibbon(self.main_container.widget)
        self.risk_ribbon.pack(fill=tk.X, pady=(0, 10))
        
        # Add separator
        separator = ttk.Separator(self.main_container.widget, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        # Content area (tabbed interface)
        self.notebook = ttk.Notebook(self.main_container.widget)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tabs
        self.create_overview_tab()
        self.create_status_tab()
        self.create_settings_tab()
        
        # Status bar (bottom)
        self.setup_status_bar()
    
    def create_overview_tab(self):
        """Create main overview tab"""
        overview_frame = ModernFrame(self.notebook)
        self.notebook.add(overview_frame.widget, text="Overview")
        
        # Welcome message
        welcome_label = ModernLabel(
            overview_frame.widget,
            text="HUEY_P Modern GUI - Ready for Trading"
        )
        welcome_label.pack(pady=20)
        
        # Basic info
        info_text = """
        This is the modernized HUEY_P Trading System GUI.
        
        Key Features:
        • Real-time risk monitoring in the ribbon above
        • Event-driven architecture for responsive updates  
        • Modern dark theme optimized for trading
        • Emergency controls always accessible
        • Integrated with existing MT4 DDE interface
        
        The risk ribbon shows:
        - Connection status to MT4
        - Daily drawdown vs limit
        - Portfolio risk level
        - Session cap usage
        """
        
        info_label = ModernLabel(
            overview_frame.widget,
            text=info_text
        )
        info_label.pack(pady=20, padx=20)
    
    def create_status_tab(self):
        """Create system status tab"""
        status_frame = ModernFrame(self.notebook)
        self.notebook.add(status_frame.widget, text="System Status")
        
        # Event bus stats
        self.event_stats_label = ModernLabel(
            status_frame.widget,
            text="Event Bus: Loading..."
        )
        self.event_stats_label.pack(pady=10)
        
        # State manager info
        self.state_info_label = ModernLabel(
            status_frame.widget,
            text="State Manager: Loading..."
        )
        self.state_info_label.pack(pady=10)
        
        # System health
        self.health_label = ModernLabel(
            status_frame.widget,
            text="System Health: Loading..."
        )
        self.health_label.pack(pady=10)
        
        # Start status updates
        self.update_status_tab()
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ModernFrame(self.notebook)
        self.notebook.add(settings_frame.widget, text="Settings")
        
        # Placeholder for settings
        settings_label = ModernLabel(
            settings_frame.widget,
            text="Settings panel - Coming soon"
        )
        settings_label.pack(pady=20)
    
    def setup_status_bar(self):
        """Setup bottom status bar"""
        self.status_frame = ModernFrame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
        
        # App status
        self.app_status_label = ModernLabel(
            self.status_frame.widget,
            text="Application started"
        )
        self.app_status_label.pack(side=tk.LEFT, padx=5)
        
        # Time display
        self.time_label = ModernLabel(
            self.status_frame.widget,
            text=""
        )
        self.time_label.pack(side=tk.RIGHT, padx=5)
        
        # Start time updates
        self.update_time()
    
    def start_services(self):
        """Start background services and data simulation"""
        # Start simulated data updates in background thread
        self.simulation_thread = threading.Thread(target=self.simulate_data_updates, daemon=True)
        self.simulation_thread.start()
        
        print("HUEY_P Modern GUI services started")
    
    def simulate_data_updates(self):
        """Simulate realistic trading data updates"""
        import random
        
        while True:
            try:
                # Simulate risk metric updates
                event_bus.publish(
                    "risk_update",
                    {
                        "daily_drawdown": random.uniform(-0.5, -2.5),
                        "portfolio_risk": random.uniform(0.1, 0.8),
                        "session_cap_used": random.uniform(0.2, 1.3),
                        "max_correlation": random.uniform(0.1, 0.8)
                    },
                    "simulator"
                )
                
                # Simulate connectivity updates
                event_bus.publish(
                    "connectivity_update",
                    {
                        "dde_connected": random.choice([True, True, True, False]),  # Mostly connected
                        "symbol_count": random.randint(8, 28),
                        "connection_quality": random.choice(["excellent", "good", "poor"])
                    },
                    "simulator"
                )
                
                # Simulate system health
                event_bus.publish(
                    "system_health_update",
                    {
                        "cpu_usage": random.uniform(10, 60),
                        "memory_usage": random.uniform(30, 80),
                        "frame_rate": random.uniform(55, 60),
                        "event_queue_size": random.randint(0, 10)
                    },
                    "simulator"
                )
                
                # Sleep before next update
                time.sleep(3 + random.uniform(0, 2))  # 3-5 seconds
                
            except Exception as e:
                print(f"Error in data simulation: {e}")
                time.sleep(5)
    
    def update_status_tab(self):
        """Update system status tab"""
        try:
            # Update event bus stats
            stats = event_bus.get_stats()
            event_text = f"Event Bus: {stats['events_published']} events published, {stats['subscribers_count']} subscribers"
            self.event_stats_label.configure(text=event_text)
            
            # Update state info
            risk = state_manager.get_risk_metrics()
            conn = state_manager.get_connectivity_status()
            state_text = f"State: DD {risk.daily_drawdown:.2f}%, Connected: {conn.dde_connected}"
            self.state_info_label.configure(text=state_text)
            
            # Update system health
            health = state_manager.get_system_health()
            health_text = f"Health: CPU {health.cpu_usage:.1f}%, Memory {health.memory_usage:.1f}%, FPS {health.frame_rate:.1f}"
            self.health_label.configure(text=health_text)
            
            # Schedule next update
            self.root.after(2000, self.update_status_tab)
            
        except Exception as e:
            print(f"Error updating status tab: {e}")
            self.root.after(5000, self.update_status_tab)
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        self.root.after(1000, self.update_time)
    
    def on_closing(self):
        """Handle application closing"""
        print("Shutting down HUEY_P Modern GUI...")
        
        # Publish shutdown event
        try:
            event_bus.publish("app_shutdown", {"timestamp": datetime.now()}, "main_app")
        except:
            pass
        
        # Destroy the window
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        print("Starting HUEY_P Modern GUI...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application interrupted by user")
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.on_closing()

def main():
    """Main entry point"""
    app = HueyPModernApp()
    app.run()

if __name__ == "__main__":
    main()