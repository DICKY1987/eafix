"""
HUEY_P Trading Interface - Live Dashboard Tab
Real-time trading status and metrics display
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from core.data_models import LiveMetrics, SystemStatus, EAState, RecoveryState
from widgets.metrics_display import MetricsDisplay
from widgets.status_indicators import StatusIndicator, StatusIndicatorGrid
from widgets.charts import PerformanceChart

logger = logging.getLogger(__name__)

class LiveDashboard:
    """Live dashboard showing real-time trading metrics"""
    
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app_controller = app_controller
        self.frame = None
        
        # Widgets
        self.metrics_display = None
        self.status_indicators = None
        self.performance_chart = None
        
        # Data
        self.last_update = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Create main layout with left panel and right panel
        self.create_layout()
        
        # Setup individual components
        self.setup_status_section()
        self.setup_metrics_section()
        self.setup_trades_section()
        self.setup_performance_section()
        
        logger.info("Live dashboard UI setup complete")
    
    def create_layout(self):
        """Create the main layout structure"""
        # Main container with padding
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row - Status indicators
        self.status_frame = ttk.LabelFrame(main_container, text="📊 System Status", padding=10)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Middle row - split into left and right
        middle_frame = ttk.Frame(main_container)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left panel - Metrics
        self.metrics_frame = ttk.LabelFrame(middle_frame, text="📈 Live Metrics", padding=10)
        self.metrics_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel - Current Trades
        self.trades_frame = ttk.LabelFrame(middle_frame, text="💼 Active Positions", padding=10)
        self.trades_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Bottom row - Performance chart
        self.performance_frame = ttk.LabelFrame(main_container, text="📊 Performance Overview", padding=10)
        self.performance_frame.pack(fill=tk.BOTH, expand=True)
    
    def setup_status_section(self):
        """Setup the status indicators section"""
        # Create status grid
        status_grid = ttk.Frame(self.status_frame)
        status_grid.pack(fill=tk.X)
        
        # EA State
        ttk.Label(status_grid, text="EA State:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.ea_state_label = ttk.Label(status_grid, text="UNKNOWN", foreground="gray")
        self.ea_state_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Recovery State
        ttk.Label(status_grid, text="Recovery:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.recovery_state_label = ttk.Label(status_grid, text="UNKNOWN", foreground="gray")
        self.recovery_state_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # Connection Status
        ttk.Label(status_grid, text="Connection:", font=('Arial', 10, 'bold')).grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.connection_label = ttk.Label(status_grid, text="DISCONNECTED", foreground="red")
        self.connection_label.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        
        # Last Update
        ttk.Label(status_grid, text="Last Update:", font=('Arial', 10, 'bold')).grid(row=0, column=6, sticky=tk.W, padx=(0, 10))
        self.last_update_label = ttk.Label(status_grid, text="Never", foreground="gray")
        self.last_update_label.grid(row=0, column=7, sticky=tk.W)
    
    def setup_metrics_section(self):
        """Setup the live metrics section"""
        # Create metrics grid
        metrics_grid = ttk.Frame(self.metrics_frame)
        metrics_grid.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        for i in range(4):
            metrics_grid.columnconfigure(i, weight=1)
        
        # Account metrics
        account_frame = ttk.LabelFrame(metrics_grid, text="Account", padding=5)
        account_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=(0, 5), pady=(0, 5))
        
        ttk.Label(account_frame, text="Equity:").grid(row=0, column=0, sticky=tk.W)
        self.equity_label = ttk.Label(account_frame, text="$0.00", font=('Arial', 12, 'bold'))
        self.equity_label.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(account_frame, text="Balance:").grid(row=1, column=0, sticky=tk.W)
        self.balance_label = ttk.Label(account_frame, text="$0.00")
        self.balance_label.grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(account_frame, text="Daily P&L:").grid(row=2, column=0, sticky=tk.W)
        self.daily_profit_label = ttk.Label(account_frame, text="$0.00")
        self.daily_profit_label.grid(row=2, column=1, sticky=tk.E)
        
        # Trading metrics
        trading_frame = ttk.LabelFrame(metrics_grid, text="Trading", padding=5)
        trading_frame.grid(row=0, column=2, columnspan=2, sticky=tk.EW, padx=(5, 0), pady=(0, 5))
        
        ttk.Label(trading_frame, text="Active Trades:").grid(row=0, column=0, sticky=tk.W)
        self.active_trades_label = ttk.Label(trading_frame, text="0", font=('Arial', 12, 'bold'))
        self.active_trades_label.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(trading_frame, text="Total Trades:").grid(row=1, column=0, sticky=tk.W)
        self.total_trades_label = ttk.Label(trading_frame, text="0")
        self.total_trades_label.grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(trading_frame, text="Win Rate:").grid(row=2, column=0, sticky=tk.W)
        self.win_rate_label = ttk.Label(trading_frame, text="0%")
        self.win_rate_label.grid(row=2, column=1, sticky=tk.E)
        
        # Risk metrics
        risk_frame = ttk.LabelFrame(metrics_grid, text="Risk Management", padding=5)
        risk_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, pady=(5, 0))
        
        risk_grid = ttk.Frame(risk_frame)
        risk_grid.pack(fill=tk.X)
        
        ttk.Label(risk_grid, text="Daily Drawdown:").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        self.drawdown_label = ttk.Label(risk_grid, text="0%")
        self.drawdown_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 40))
        
        ttk.Label(risk_grid, text="Risk Percent:").grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        self.risk_percent_label = ttk.Label(risk_grid, text="0%")
        self.risk_percent_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 40))
        
        ttk.Label(risk_grid, text="Uptime:").grid(row=0, column=4, sticky=tk.W, padx=(0, 20))
        self.uptime_label = ttk.Label(risk_grid, text="0s")
        self.uptime_label.grid(row=0, column=5, sticky=tk.W)
    
    def setup_trades_section(self):
        """Setup the current trades section"""
        # Create treeview for current positions
        columns = ('Symbol', 'Type', 'Volume', 'Price', 'P&L')
        self.trades_tree = ttk.Treeview(self.trades_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        for col in columns:
            self.trades_tree.heading(col, text=col)
            if col == 'Symbol':
                self.trades_tree.column(col, width=80)
            elif col == 'Type':
                self.trades_tree.column(col, width=60)
            elif col == 'Volume':
                self.trades_tree.column(col, width=70)
            elif col == 'Price':
                self.trades_tree.column(col, width=80)
            elif col == 'P&L':
                self.trades_tree.column(col, width=80)
        
        # Add scrollbar
        trades_scrollbar = ttk.Scrollbar(self.trades_frame, orient=tk.VERTICAL, command=self.trades_tree.yview)
        self.trades_tree.configure(yscrollcommand=trades_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.trades_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trades_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary frame below trades
        trades_summary = ttk.Frame(self.trades_frame)
        trades_summary.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(trades_summary, text="Total Exposure:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.total_exposure_label = ttk.Label(trades_summary, text="$0.00")
        self.total_exposure_label.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(trades_summary, text="Unrealized P&L:", font=('Arial', 9, 'bold')).pack(side=tk.RIGHT)
        self.unrealized_pl_label = ttk.Label(trades_summary, text="$0.00")
        self.unrealized_pl_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def setup_performance_section(self):
        """Setup the performance overview section"""
        # For now, create a simple text display
        # In full implementation, this would be a matplotlib chart
        
        perf_text = tk.Text(self.performance_frame, height=6, wrap=tk.WORD)
        perf_text.pack(fill=tk.BOTH, expand=True)
        
        # Insert placeholder text
        perf_text.insert(tk.END, "Performance Chart Placeholder\n\n")
        perf_text.insert(tk.END, "This area will display:\n")
        perf_text.insert(tk.END, "• Equity curve over time\n")
        perf_text.insert(tk.END, "• Daily P&L chart\n")
        perf_text.insert(tk.END, "• Drawdown visualization\n")
        perf_text.insert(tk.END, "• Trade distribution analysis")
        
        perf_text.config(state=tk.DISABLED)
        
        self.performance_text = perf_text
    
    def update_data(self, live_metrics: LiveMetrics, system_status: SystemStatus):
        """Update dashboard with new data"""
        try:
            self.update_status_indicators(live_metrics, system_status)
            self.update_metrics_display(live_metrics)
            self.update_trades_display()
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating live dashboard: {e}")
    
    def update_status_indicators(self, live_metrics: LiveMetrics, system_status: SystemStatus):
        """Update status indicator section"""
        # EA State
        ea_state_text = live_metrics.ea_state.value if live_metrics.ea_state else "UNKNOWN"
        ea_state_color = self.get_state_color(live_metrics.ea_state)
        self.ea_state_label.config(text=ea_state_text, foreground=ea_state_color)
        
        # Recovery State
        recovery_state_text = live_metrics.recovery_state.value if live_metrics.recovery_state else "UNKNOWN"
        recovery_color = self.get_recovery_color(live_metrics.recovery_state)
        self.recovery_state_label.config(text=recovery_state_text, foreground=recovery_color)
        
        # Connection Status
        if system_status.database_connected and system_status.ea_bridge_connected:
            self.connection_label.config(text="CONNECTED", foreground="green")
        elif system_status.database_connected or system_status.ea_bridge_connected:
            self.connection_label.config(text="PARTIAL", foreground="orange")
        else:
            self.connection_label.config(text="DISCONNECTED", foreground="red")
        
        # Last Update
        if live_metrics.last_update:
            update_text = live_metrics.last_update.strftime("%H:%M:%S")
            self.last_update_label.config(text=update_text, foreground="black")
        else:
            self.last_update_label.config(text="Never", foreground="gray")
    
    def update_metrics_display(self, live_metrics: LiveMetrics):
        """Update metrics display section"""
        # Account metrics
        self.equity_label.config(text=f"${live_metrics.account_equity:,.2f}")
        self.balance_label.config(text=f"${live_metrics.account_balance:,.2f}")
        
        # Color daily profit based on positive/negative
        daily_color = "green" if live_metrics.daily_profit >= 0 else "red"
        daily_sign = "+" if live_metrics.daily_profit >= 0 else ""
        self.daily_profit_label.config(text=f"{daily_sign}${live_metrics.daily_profit:,.2f}", foreground=daily_color)
        
        # Trading metrics
        self.active_trades_label.config(text=str(live_metrics.active_trades))
        self.total_trades_label.config(text=str(live_metrics.trade_count))
        self.win_rate_label.config(text=f"{live_metrics.win_rate:.1f}%")
        
        # Risk metrics
        drawdown_color = "red" if live_metrics.daily_drawdown > 5 else "black"
        self.drawdown_label.config(text=f"{live_metrics.daily_drawdown:.2f}%", foreground=drawdown_color)
        self.risk_percent_label.config(text=f"{live_metrics.risk_percent:.1f}%")
        self.uptime_label.config(text=live_metrics.uptime_formatted)
    
    def update_trades_display(self):
        """Update current trades display"""
        # Clear existing items
        for item in self.trades_tree.get_children():
            self.trades_tree.delete(item)
        
        # Get current positions from database
        db_manager = self.app_controller.get_database_manager()
        if db_manager and db_manager.is_connected():
            try:
                positions_df = db_manager.get_current_positions()
                
                total_exposure = 0.0
                total_unrealized = 0.0
                
                for _, position in positions_df.iterrows():
                    # Format values
                    symbol = position.get('symbol', 'N/A')
                    order_type = position.get('order_type', 'N/A')
                    volume = f"{position.get('volume', 0):.2f}"
                    price = f"{position.get('open_price', 0):.4f}"
                    
                    # Calculate unrealized P&L (simplified)
                    unrealized = position.get('current_profit', 0)
                    total_unrealized += unrealized
                    
                    # Calculate exposure (simplified)
                    exposure = position.get('volume', 0) * position.get('open_price', 0) * 100000  # Assuming standard lot
                    total_exposure += exposure
                    
                    # Color code P&L
                    pl_color = "green" if unrealized >= 0 else "red"
                    pl_text = f"${unrealized:,.2f}"
                    
                    # Insert into treeview
                    item = self.trades_tree.insert('', tk.END, values=(symbol, order_type, volume, price, pl_text))
                    
                    # Apply color to P&L column
                    if unrealized < 0:
                        self.trades_tree.set(item, 'P&L', pl_text)
                
                # Update summary
                self.total_exposure_label.config(text=f"${total_exposure:,.0f}")
                
                unrealized_color = "green" if total_unrealized >= 0 else "red"
                unrealized_sign = "+" if total_unrealized >= 0 else ""
                self.unrealized_pl_label.config(
                    text=f"{unrealized_sign}${total_unrealized:,.2f}", 
                    foreground=unrealized_color
                )
                
            except Exception as e:
                logger.error(f"Error updating trades display: {e}")
        else:
            # No database connection
            self.total_exposure_label.config(text="N/A")
            self.unrealized_pl_label.config(text="N/A")
    
    def get_state_color(self, state: EAState) -> str:
        """Get color for EA state"""
        if state == EAState.IDLE:
            return "blue"
        elif state == EAState.ORDERS_PLACED:
            return "orange"
        elif state == EAState.TRADE_TRIGGERED:
            return "green"
        elif state == EAState.PAUSED:
            return "red"
        else:
            return "gray"
    
    def get_recovery_color(self, state: RecoveryState) -> str:
        """Get color for recovery state"""
        if state == RecoveryState.NORMAL:
            return "green"
        elif state == RecoveryState.DEGRADED:
            return "orange"
        elif state == RecoveryState.EMERGENCY:
            return "red"
        else:
            return "gray"
    
    def refresh_data(self):
        """Force refresh of all data"""
        logger.info("Refreshing live dashboard data")
        # This will be called by the app controller during updates