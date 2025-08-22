"""
HUEY_P Trading Interface - Trade History Tab
Historical trade analysis and performance metrics
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TradeHistory:
    """Trade history and performance analysis tab"""
    
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app_controller = app_controller
        self.frame = None
        
        # Data
        self.trades_df = pd.DataFrame()
        self.performance_df = pd.DataFrame()
        self.symbol_performance_df = pd.DataFrame()
        
        # Filter settings
        self.filter_days = tk.StringVar(value="30")
        self.filter_symbol = tk.StringVar(value="All")
        self.filter_result = tk.StringVar(value="All")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the trade history UI"""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Create layout
        self.create_layout()
        
        # Setup components
        self.setup_filter_section()
        self.setup_trades_table()
        self.setup_analysis_section()
        
        logger.info("Trade history UI setup complete")
    
    def create_layout(self):
        """Create the main layout structure"""
        # Main container with padding
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row - Filters and controls
        self.filter_frame = ttk.LabelFrame(main_container, text="🔍 Filters & Controls", padding=10)
        self.filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Middle row - Trades table
        self.table_frame = ttk.LabelFrame(main_container, text="📋 Trade History", padding=10)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Bottom row - Analysis split into left and right
        analysis_container = ttk.Frame(main_container)
        analysis_container.pack(fill=tk.X, pady=(0, 0))
        
        # Left analysis panel
        self.stats_frame = ttk.LabelFrame(analysis_container, text="📊 Performance Statistics", padding=10)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right analysis panel
        self.symbol_frame = ttk.LabelFrame(analysis_container, text="💱 Symbol Analysis", padding=10)
        self.symbol_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    def setup_filter_section(self):
        """Setup filter controls"""
        # Create filter controls grid
        filter_grid = ttk.Frame(self.filter_frame)
        filter_grid.pack(fill=tk.X)
        
        # Time period filter
        ttk.Label(filter_grid, text="Time Period:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        period_combo = ttk.Combobox(filter_grid, textvariable=self.filter_days, 
                                   values=["7", "30", "90", "180", "365", "All"], 
                                   width=10, state="readonly")
        period_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        period_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Symbol filter
        ttk.Label(filter_grid, text="Symbol:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.symbol_combo = ttk.Combobox(filter_grid, textvariable=self.filter_symbol, 
                                        width=12, state="readonly")
        self.symbol_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        self.symbol_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Result filter
        ttk.Label(filter_grid, text="Result:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        result_combo = ttk.Combobox(filter_grid, textvariable=self.filter_result,
                                   values=["All", "Wins", "Losses"], 
                                   width=10, state="readonly")
        result_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        result_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Refresh button
        refresh_btn = ttk.Button(filter_grid, text="🔄 Refresh", command=self.refresh_data)
        refresh_btn.grid(row=0, column=6, sticky=tk.W, padx=(20, 0))
        
        # Export button
        export_btn = ttk.Button(filter_grid, text="📤 Export", command=self.export_data)
        export_btn.grid(row=0, column=7, sticky=tk.W, padx=(10, 0))
    
    def setup_trades_table(self):
        """Setup the trades history table"""
        # Create frame for table and scrollbars
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = ('Ticket', 'Symbol', 'Type', 'Volume', 'Open Price', 'Close Price', 
                  'Open Time', 'Close Time', 'Profit', 'Commission', 'Swap', 'Net P&L', 'Comment')
        
        # Create treeview
        self.trades_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=12)
        
        # Configure column headings and widths
        column_widths = {
            'Ticket': 80,
            'Symbol': 80,
            'Type': 70,
            'Volume': 70,
            'Open Price': 90,
            'Close Price': 90,
            'Open Time': 120,
            'Close Time': 120,
            'Profit': 80,
            'Commission': 80,
            'Swap': 60,
            'Net P&L': 80,
            'Comment': 120
        }
        
        for col in columns:
            self.trades_tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.trades_tree.column(col, width=column_widths.get(col, 100))
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.trades_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.trades_tree.xview)
        
        self.trades_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack table and scrollbars
        self.trades_tree.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        # Configure grid weights
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # Summary row
        summary_frame = ttk.Frame(self.table_frame)
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(summary_frame, text="Total Trades:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.total_trades_label = ttk.Label(summary_frame, text="0")
        self.total_trades_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(summary_frame, text="Total P&L:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.total_pl_label = ttk.Label(summary_frame, text="$0.00")
        self.total_pl_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_analysis_section(self):
        """Setup the analysis panels"""
        # Performance statistics
        self.setup_performance_stats()
        
        # Symbol analysis
        self.setup_symbol_analysis()
    
    def setup_performance_stats(self):
        """Setup performance statistics panel"""
        stats_grid = ttk.Frame(self.stats_frame)
        stats_grid.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid
        for i in range(3):
            stats_grid.columnconfigure(i, weight=1)
        
        # Win/Loss Statistics
        win_loss_frame = ttk.LabelFrame(stats_grid, text="Win/Loss", padding=5)
        win_loss_frame.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5), pady=(0, 5))
        
        ttk.Label(win_loss_frame, text="Wins:").grid(row=0, column=0, sticky=tk.W)
        self.wins_label = ttk.Label(win_loss_frame, text="0")
        self.wins_label.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(win_loss_frame, text="Losses:").grid(row=1, column=0, sticky=tk.W)
        self.losses_label = ttk.Label(win_loss_frame, text="0")
        self.losses_label.grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(win_loss_frame, text="Win Rate:").grid(row=2, column=0, sticky=tk.W)
        self.win_rate_stats_label = ttk.Label(win_loss_frame, text="0%", font=('Arial', 10, 'bold'))
        self.win_rate_stats_label.grid(row=2, column=1, sticky=tk.E)
        
        # Profit Statistics
        profit_frame = ttk.LabelFrame(stats_grid, text="Profit", padding=5)
        profit_frame.grid(row=0, column=1, sticky=tk.EW, padx=(2, 3), pady=(0, 5))
        
        ttk.Label(profit_frame, text="Avg Win:").grid(row=0, column=0, sticky=tk.W)
        self.avg_win_label = ttk.Label(profit_frame, text="$0.00")
        self.avg_win_label.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(profit_frame, text="Avg Loss:").grid(row=1, column=0, sticky=tk.W)
        self.avg_loss_label = ttk.Label(profit_frame, text="$0.00")
        self.avg_loss_label.grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(profit_frame, text="Profit Factor:").grid(row=2, column=0, sticky=tk.W)
        self.profit_factor_label = ttk.Label(profit_frame, text="0.00", font=('Arial', 10, 'bold'))
        self.profit_factor_label.grid(row=2, column=1, sticky=tk.E)
        
        # Risk Statistics
        risk_frame = ttk.LabelFrame(stats_grid, text="Risk", padding=5)
        risk_frame.grid(row=0, column=2, sticky=tk.EW, padx=(5, 0), pady=(0, 5))
        
        ttk.Label(risk_frame, text="Max Win:").grid(row=0, column=0, sticky=tk.W)
        self.max_win_label = ttk.Label(risk_frame, text="$0.00")
        self.max_win_label.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(risk_frame, text="Max Loss:").grid(row=1, column=0, sticky=tk.W)
        self.max_loss_label = ttk.Label(risk_frame, text="$0.00")
        self.max_loss_label.grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(risk_frame, text="Avg Trade:").grid(row=2, column=0, sticky=tk.W)
        self.avg_trade_label = ttk.Label(risk_frame, text="$0.00", font=('Arial', 10, 'bold'))
        self.avg_trade_label.grid(row=2, column=1, sticky=tk.E)
        
        # Time Statistics
        time_frame = ttk.LabelFrame(stats_grid, text="Time Analysis", padding=5)
        time_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(5, 0))
        
        time_grid = ttk.Frame(time_frame)
        time_grid.pack(fill=tk.X)
        
        ttk.Label(time_grid, text="Avg Duration:").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        self.avg_duration_label = ttk.Label(time_grid, text="0 min")
        self.avg_duration_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 40))
        
        ttk.Label(time_grid, text="Best Hour:").grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        self.best_hour_label = ttk.Label(time_grid, text="N/A")
        self.best_hour_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 40))
        
        ttk.Label(time_grid, text="Best Day:").grid(row=0, column=4, sticky=tk.W, padx=(0, 20))
        self.best_day_label = ttk.Label(time_grid, text="N/A")
        self.best_day_label.grid(row=0, column=5, sticky=tk.W)
    
    def setup_symbol_analysis(self):
        """Setup symbol analysis panel"""
        # Create treeview for symbol performance
        symbol_columns = ('Symbol', 'Trades', 'Wins', 'Losses', 'Win Rate', 'Net P&L', 'Avg P&L')
        self.symbol_tree = ttk.Treeview(self.symbol_frame, columns=symbol_columns, show='headings', height=8)
        
        # Configure columns
        symbol_widths = {
            'Symbol': 80,
            'Trades': 60,
            'Wins': 50,
            'Losses': 50,
            'Win Rate': 70,
            'Net P&L': 90,
            'Avg P&L': 80
        }
        
        for col in symbol_columns:
            self.symbol_tree.heading(col, text=col, command=lambda c=col: self.sort_symbol_column(c))
            self.symbol_tree.column(col, width=symbol_widths.get(col, 80))
        
        # Add scrollbar for symbol analysis
        symbol_scrollbar = ttk.Scrollbar(self.symbol_frame, orient=tk.VERTICAL, command=self.symbol_tree.yview)
        self.symbol_tree.configure(yscrollcommand=symbol_scrollbar.set)
        
        # Pack symbol treeview and scrollbar
        self.symbol_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        symbol_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def refresh_data(self):
        """Refresh all trade history data"""
        logger.info("Refreshing trade history data")
        
        try:
            db_manager = self.app_controller.get_database_manager()
            if not db_manager or not db_manager.is_connected():
                logger.warning("Database not connected, cannot refresh trade history")
                return
            
            # Get filtered data based on current filter settings
            self.load_trades_data()
            self.load_performance_data()
            self.load_symbol_data()
            
            # Update displays
            self.update_trades_table()
            self.update_performance_stats()
            self.update_symbol_analysis()
            self.update_symbol_filter()
            
        except Exception as e:
            logger.error(f"Error refreshing trade history data: {e}")
    
    def load_trades_data(self):
        """Load trades data from database"""
        db_manager = self.app_controller.get_database_manager()
        
        # Determine limit based on filter
        days_filter = self.filter_days.get()
        if days_filter == "All":
            limit = 1000  # Large number for "all"
        else:
            limit = int(days_filter) * 10  # Approximate trades per day
        
        self.trades_df = db_manager.get_recent_trades(limit=limit)
        
        # Apply additional filters
        self.apply_filters()
    
    def load_performance_data(self):
        """Load performance data from database"""
        db_manager = self.app_controller.get_database_manager()
        
        days_filter = self.filter_days.get()
        days = 365 if days_filter == "All" else int(days_filter)
        
        self.performance_df = db_manager.get_daily_performance(days=days)
    
    def load_symbol_data(self):
        """Load symbol performance data"""
        db_manager = self.app_controller.get_database_manager()
        self.symbol_performance_df = db_manager.get_symbol_performance()
    
    def apply_filters(self):
        """Apply current filters to trades data"""
        if self.trades_df.empty:
            return
        
        filtered_df = self.trades_df.copy()
        
        # Apply time filter
        days_filter = self.filter_days.get()
        if days_filter != "All":
            cutoff_date = datetime.now() - timedelta(days=int(days_filter))
            filtered_df = filtered_df[filtered_df['close_time'] >= cutoff_date]
        
        # Apply symbol filter
        symbol_filter = self.filter_symbol.get()
        if symbol_filter != "All":
            filtered_df = filtered_df[filtered_df['symbol'] == symbol_filter]
        
        # Apply result filter
        result_filter = self.filter_result.get()
        if result_filter == "Wins":
            filtered_df = filtered_df[filtered_df['profit'] > 0]
        elif result_filter == "Losses":
            filtered_df = filtered_df[filtered_df['profit'] <= 0]
        
        self.trades_df = filtered_df
    
    def update_trades_table(self):
        """Update the trades table display"""
        # Clear existing items
        for item in self.trades_tree.get_children():
            self.trades_tree.delete(item)
        
        if self.trades_df.empty:
            self.total_trades_label.config(text="0")
            self.total_pl_label.config(text="$0.00")
            return
        
        total_pl = 0.0
        
        # Add trades to table
        for _, trade in self.trades_df.iterrows():
            # Calculate net P&L
            net_pl = (trade.get('profit', 0) + 
                     trade.get('commission', 0) + 
                     trade.get('swap', 0))
            total_pl += net_pl
            
            # Format values
            values = (
                str(trade.get('ticket', '')),
                trade.get('symbol', ''),
                trade.get('order_type', ''),
                f"{trade.get('volume', 0):.2f}",
                f"{trade.get('open_price', 0):.4f}",
                f"{trade.get('close_price', 0):.4f}",
                trade.get('open_time', '').strftime('%Y-%m-%d %H:%M') if pd.notna(trade.get('open_time')) else '',
                trade.get('close_time', '').strftime('%Y-%m-%d %H:%M') if pd.notna(trade.get('close_time')) else '',
                f"{trade.get('profit', 0):.2f}",
                f"{trade.get('commission', 0):.2f}",
                f"{trade.get('swap', 0):.2f}",
                f"{net_pl:.2f}",
                trade.get('comment', '')
            )
            
            item = self.trades_tree.insert('', tk.END, values=values)
            
            # Color code the row based on profit/loss
            if net_pl > 0:
                self.trades_tree.set(item, 'Net P&L', f"+{net_pl:.2f}")
            else:
                self.trades_tree.set(item, 'Net P&L', f"{net_pl:.2f}")
        
        # Update summary
        self.total_trades_label.config(text=str(len(self.trades_df)))
        
        total_color = "green" if total_pl >= 0 else "red"
        total_sign = "+" if total_pl >= 0 else ""
        self.total_pl_label.config(text=f"{total_sign}${total_pl:,.2f}", foreground=total_color)
    
    def update_performance_stats(self):
        """Update performance statistics"""
        if self.trades_df.empty:
            # Reset all labels to zero
            self.wins_label.config(text="0")
            self.losses_label.config(text="0")
            self.win_rate_stats_label.config(text="0%")
            self.avg_win_label.config(text="$0.00")
            self.avg_loss_label.config(text="$0.00")
            self.profit_factor_label.config(text="0.00")
            self.max_win_label.config(text="$0.00")
            self.max_loss_label.config(text="$0.00")
            self.avg_trade_label.config(text="$0.00")
            self.avg_duration_label.config(text="0 min")
            self.best_hour_label.config(text="N/A")
            self.best_day_label.config(text="N/A")
            return
        
        # Calculate statistics
        profits = self.trades_df['profit'] + self.trades_df['commission'] + self.trades_df['swap']
        
        wins = profits[profits > 0]
        losses = profits[profits <= 0]
        
        total_wins = len(wins)
        total_losses = len(losses)
        total_trades = len(profits)
        
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        max_win = profits.max() if not profits.empty else 0
        max_loss = profits.min() if not profits.empty else 0
        avg_trade = profits.mean() if not profits.empty else 0
        
        # Update labels
        self.wins_label.config(text=str(total_wins))
        self.losses_label.config(text=str(total_losses))
        self.win_rate_stats_label.config(text=f"{win_rate:.1f}%")
        self.avg_win_label.config(text=f"${avg_win:.2f}")
        self.avg_loss_label.config(text=f"${avg_loss:.2f}")
        self.profit_factor_label.config(text=f"{profit_factor:.2f}")
        self.max_win_label.config(text=f"${max_win:.2f}")
        self.max_loss_label.config(text=f"${max_loss:.2f}")
        
        avg_color = "green" if avg_trade >= 0 else "red"
        self.avg_trade_label.config(text=f"${avg_trade:.2f}", foreground=avg_color)
        
        # Time analysis (simplified)
        if 'open_time' in self.trades_df.columns and 'close_time' in self.trades_df.columns:
            # Calculate average duration
            durations = []
            for _, trade in self.trades_df.iterrows():
                if pd.notna(trade['open_time']) and pd.notna(trade['close_time']):
                    duration = (trade['close_time'] - trade['open_time']).total_seconds() / 60
                    durations.append(duration)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                self.avg_duration_label.config(text=f"{avg_duration:.0f} min")
            
            # Best performing hour and day (simplified analysis)
            if not self.trades_df.empty:
                # Group by hour
                self.trades_df['hour'] = pd.to_datetime(self.trades_df['close_time']).dt.hour
                hourly_profit = self.trades_df.groupby('hour')['profit'].sum()
                best_hour = hourly_profit.idxmax() if not hourly_profit.empty else None
                
                # Group by day of week
                self.trades_df['day_of_week'] = pd.to_datetime(self.trades_df['close_time']).dt.day_name()
                daily_profit = self.trades_df.groupby('day_of_week')['profit'].sum()
                best_day = daily_profit.idxmax() if not daily_profit.empty else None
                
                self.best_hour_label.config(text=f"{best_hour}:00" if best_hour is not None else "N/A")
                self.best_day_label.config(text=str(best_day) if best_day is not None else "N/A")
    
    def update_symbol_analysis(self):
        """Update symbol analysis table"""
        # Clear existing items
        for item in self.symbol_tree.get_children():
            self.symbol_tree.delete(item)
        
        if self.symbol_performance_df.empty:
            return
        
        # Add symbol data to table
        for _, symbol_data in self.symbol_performance_df.iterrows():
            values = (
                symbol_data.get('symbol', ''),
                str(symbol_data.get('trade_count', 0)),
                str(symbol_data.get('wins', 0)),
                str(symbol_data.get('losses', 0)),
                f"{symbol_data.get('win_rate', 0):.1f}%",
                f"${symbol_data.get('net_profit', 0):.2f}",
                f"${symbol_data.get('avg_profit', 0):.2f}"
            )
            
            self.symbol_tree.insert('', tk.END, values=values)
    
    def update_symbol_filter(self):
        """Update symbol filter dropdown with available symbols"""
        if not self.trades_df.empty:
            symbols = ['All'] + sorted(self.trades_df['symbol'].unique().tolist())
            self.symbol_combo['values'] = symbols
    
    def on_filter_changed(self, event=None):
        """Handle filter change event"""
        self.refresh_data()
    
    def sort_by_column(self, column):
        """Sort trades table by column"""
        # This would implement sorting functionality
        logger.info(f"Sorting by column: {column}")
    
    def sort_symbol_column(self, column):
        """Sort symbol table by column"""
        # This would implement sorting functionality
        logger.info(f"Sorting symbol table by column: {column}")
    
    def export_data(self):
        """Export current trade data"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                self.trades_df.to_csv(filename, index=False)
                logger.info(f"Trade data exported to: {filename}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")