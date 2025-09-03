"""
HUEY_P Trading Interface - Application Controller
Manages the main application logic and tab coordination
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio

from .database_manager import DatabaseManager
from .ea_connector import EAConnector
from .data_models import SystemStatus as SystemStatusData, LiveMetrics, TradeData
from .constraint_repository import TradingConstraintRepository

from tabs.live_dashboard import LiveDashboard
from tabs.trade_history import TradeHistory
from tabs.system_status import SystemStatusTab
from tabs.settings_panel import SettingsPanel
from tabs.economic_calendar import EconomicCalendar
from tabs.dde_price_feed import create_dde_tab
from tabs.indicator_tab import IndicatorsTab

logger = logging.getLogger(__name__)

class AppController:
    """Main application controller that manages all components"""
    
    def __init__(self, root: tk.Tk, config: Dict[str, Any]):
        self.root = root
        self.config = config
        self.notebook = None
        
        # Core components
        self.db_manager = None
        self.ea_connector = None
        
        # Tabs
        self.live_dashboard = None
        self.trade_history = None
        self.system_status = None
        self.settings_panel = None
        self.economic_calendar = None
        self.indicators_tab = None
        
        # Data containers
        self.system_status_data = SystemStatusData()
        self.live_metrics_data = LiveMetrics()

        # Constraint repository
        self.constraint_repo = None
        
        # Update control
        self.update_thread = None
        self.running = False
        self.last_update = datetime.now()
        
        # Status tracking
        self.connection_status = {
            'database': False,
            'ea_bridge': False,
            'last_heartbeat': None
        }
        
    def initialize(self):
        """Initialize all application components"""
        logger.info("Initializing application controller")
        
        try:
            # Setup main UI structure
            self.setup_main_ui()
            
            # Initialize core components
            self.initialize_core_components()
            
            # Initialize tabs
            self.initialize_tabs()
            
            # Start background update thread
            self.start_update_thread()
            
            # Initial data load
            self.refresh_all_data()
            
            logger.info("Application controller initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application controller: {e}")
            raise
    
    def setup_main_ui(self):
        """Setup the main UI structure with tabs"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create status bar
        self.create_status_bar(main_frame)
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_status_bar(self, parent):
        """Create bottom status bar"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Connection status indicators
        ttk.Label(self.status_frame, text="DB:").pack(side=tk.LEFT)
        self.db_status_label = ttk.Label(self.status_frame, text="●", foreground="red")
        self.db_status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(self.status_frame, text="EA:").pack(side=tk.LEFT)
        self.ea_status_label = ttk.Label(self.status_frame, text="●", foreground="red")
        self.ea_status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Last update time
        self.update_time_label = ttk.Label(self.status_frame, text="Last update: Never")
        self.update_time_label.pack(side=tk.RIGHT)
        
        # Current time
        self.current_time_label = ttk.Label(self.status_frame, text="")
        self.current_time_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Update current time
        self.update_current_time()
    
    def update_current_time(self):
        """Update current time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=current_time)
        self.root.after(1000, self.update_current_time)
    
    def initialize_core_components(self):
        """Initialize database and EA connector"""
        # Initialize database manager
        self.db_manager = DatabaseManager(self.config['database'])
        if self.db_manager.connect():
            self.connection_status['database'] = True
            logger.info("Database connected successfully")
        else:
            logger.warning("Database connection failed")

        # Initialize constraint repository
        self.constraint_repo = TradingConstraintRepository(
            self.config.get('constraint_db', 'trading_constraints.db')
        )

        # Initialize EA connector
        self.ea_connector = EAConnector(
            self.config['ea_bridge'], constraint_repo=self.constraint_repo
        )
        if self.ea_connector.connect():
            self.connection_status['ea_bridge'] = True
            logger.info("EA bridge connected successfully")
        else:
            logger.warning("EA bridge connection failed")
    
    def initialize_tabs(self):
        """Initialize all tab components"""
        # Tab 1: Live Dashboard
        self.live_dashboard = LiveDashboard(self.notebook, self)
        self.notebook.add(self.live_dashboard.frame, text="📊 Live Dashboard")
        
        # Tab 2: Trade History
        self.trade_history = TradeHistory(self.notebook, self)
        self.notebook.add(self.trade_history.frame, text="📈 Trade History")
        
        # Tab 3: System Status
        self.system_status = SystemStatusTab(self.notebook, self)
        self.notebook.add(self.system_status.frame, text="⚡ System Status")
        
        # Tab 4: DDE Price Feed
        self.dde_price_feed = create_dde_tab(self.notebook)
        
        # Tab 5: Economic Calendar
        self.economic_calendar = EconomicCalendar(self.notebook, self)
        self.notebook.add(self.economic_calendar.frame, text="📅 Economic Calendar")

        # Tab 6: Indicators
        self.indicators_tab = IndicatorsTab(self.notebook, self)
        self.notebook.add(self.indicators_tab.frame, text="📐 Indicators")

        # Tab 7: Settings
        self.settings_panel = SettingsPanel(self.notebook, self)
        self.notebook.add(self.settings_panel.frame, text="⚙️ Settings")
        
        logger.info("All tabs initialized successfully")
    
    def start_update_thread(self):
        """Start background update thread"""
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Background update thread started")
    
    def update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                # Update system status
                self.update_system_status()
                
                # Update live metrics if EA is connected
                if self.connection_status['ea_bridge']:
                    self.update_live_metrics()
                
                # Update status bar
                self.root.after(0, self.update_status_bar)
                
                # Update active tab
                self.root.after(0, self.update_active_tab)
                
                # Record last update time
                self.last_update = datetime.now()
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
            
            # Wait for next update
            time.sleep(self.config['app']['refresh_interval'] / 1000.0)
    
    def update_system_status(self):
        """Update system status data"""
        try:
            # Check database connection
            if self.db_manager:
                self.connection_status['database'] = self.db_manager.is_connected()
            
            # Check EA connection and get heartbeat
            if self.ea_connector:
                heartbeat = self.ea_connector.get_heartbeat()
                if heartbeat:
                    self.connection_status['ea_bridge'] = True
                    self.connection_status['last_heartbeat'] = datetime.now()
                    self.system_status_data.update_from_heartbeat(heartbeat)
                else:
                    self.connection_status['ea_bridge'] = False
                    
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def update_live_metrics(self):
        """Update live trading metrics"""
        try:
            if self.ea_connector:
                # Get live metrics from EA
                metrics = self.ea_connector.get_live_metrics()
                if metrics:
                    self.live_metrics_data.update_from_dict(metrics)
                    
        except Exception as e:
            logger.error(f"Error updating live metrics: {e}")
    
    def update_status_bar(self):
        """Update status bar indicators"""
        # Database status
        db_color = "green" if self.connection_status['database'] else "red"
        self.db_status_label.config(foreground=db_color)
        
        # EA status
        ea_color = "green" if self.connection_status['ea_bridge'] else "red"
        self.ea_status_label.config(foreground=ea_color)
        
        # Last update time
        update_str = self.last_update.strftime("%H:%M:%S")
        self.update_time_label.config(text=f"Last update: {update_str}")
    
    def update_active_tab(self):
        """Update the currently active tab"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return
                
            tab_index = self.notebook.index(current_tab)
            
            # Update specific tab
            if tab_index == 0 and self.live_dashboard:
                self.live_dashboard.update_data(self.live_metrics_data, self.system_status_data)
            elif tab_index == 1 and self.trade_history:
                # Trade history updates less frequently
                if datetime.now() - self.last_update > timedelta(seconds=5):
                    self.trade_history.refresh_data()
            elif tab_index == 2 and self.system_status:
                self.system_status.update_data(self.system_status_data, self.connection_status)
            elif tab_index == 3 and hasattr(self.dde_price_feed, 'refresh_data'):
                self.dde_price_feed.refresh_data()
            elif tab_index == 4 and self.economic_calendar:
                # Economic calendar doesn't need frequent updates
                pass
            elif tab_index == 5 and self.settings_panel:
                # Settings panel doesn't need frequent updates
                pass
                
        except Exception as e:
            logger.error(f"Error updating active tab: {e}")
    
    def on_tab_changed(self, event):
        """Handle tab change event"""
        try:
            current_tab = self.notebook.select()
            tab_index = self.notebook.index(current_tab)
            tab_text = self.notebook.tab(current_tab, "text")
            
            logger.debug(f"Tab changed to: {tab_text}")
            
            # Force immediate update of new tab
            if tab_index == 1 and self.trade_history:
                self.trade_history.refresh_data()
            elif tab_index == 2 and self.system_status:
                self.system_status.refresh_data()
            elif tab_index == 3 and hasattr(self.dde_price_feed, 'refresh_data'):
                self.dde_price_feed.refresh_data()
            elif tab_index == 4 and self.economic_calendar:
                self.economic_calendar.refresh_data()
                
        except Exception as e:
            logger.error(f"Error handling tab change: {e}")
    
    def refresh_all_data(self):
        """Force refresh of all data"""
        logger.info("Refreshing all data")
        
        try:
            # Refresh each tab
            if self.live_dashboard:
                self.live_dashboard.refresh_data()
            if self.trade_history:
                self.trade_history.refresh_data()
            if self.system_status:
                self.system_status.refresh_data()
            if hasattr(self.dde_price_feed, 'refresh_data'):
                self.dde_price_feed.refresh_data()
            if self.economic_calendar:
                self.economic_calendar.refresh_data()
            if self.settings_panel:
                self.settings_panel.refresh_data()
                
        except Exception as e:
            logger.error(f"Error refreshing all data: {e}")
    
    def get_database_manager(self) -> Optional[DatabaseManager]:
        """Get database manager instance"""
        return self.db_manager
    
    def get_ea_connector(self) -> Optional[EAConnector]:
        """Get EA connector instance"""
        return self.ea_connector
    
    def get_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return self.config
    
    def show_error(self, title: str, message: str):
        """Show error message to user"""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """Show info message to user"""
        messagebox.showinfo(title, message)
    
    def shutdown(self):
        """Shutdown application gracefully"""
        logger.info("Shutting down application controller")
        
        # Stop update thread
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)
        
        # Cleanup tabs
        if hasattr(self.dde_price_feed, 'cleanup'):
            self.dde_price_feed.cleanup()
        
        # Close connections
        if self.ea_connector:
            self.ea_connector.disconnect()

        if self.db_manager:
            self.db_manager.disconnect()

        if self.constraint_repo:
            self.constraint_repo.close()
        
        logger.info("Application controller shutdown complete")
