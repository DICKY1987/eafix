"""
Main Tab Interface for MT4 DDE Price Import with Technical Indicators
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from .dde_client import MT4DDEClient, DDEConnectionManager
    from .price_manager import PriceManager
    from .indicator_engine import IndicatorEngine, create_default_indicator_set
    from .ui_components import (
        ConnectionStatusWidget, SymbolSelectorWidget, PriceGridWidget,
        IndicatorPanelWidget, RealTimeChartWidget
    )
except ImportError:
    from dde_client import MT4DDEClient, DDEConnectionManager
    from price_manager import PriceManager
    from indicator_engine import IndicatorEngine, create_default_indicator_set
    from ui_components import (
        ConnectionStatusWidget, SymbolSelectorWidget, PriceGridWidget,
        IndicatorPanelWidget, RealTimeChartWidget
    )


class DDEPriceImportTab(ttk.Frame):
    """Main DDE Price Import Tab with Technical Indicators"""
    
    def __init__(self, parent, config_file: str = "config/settings.json", **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.config_file = config_file
        self.config = self._load_config()
        
        # Core components
        self.dde_client = None
        self.connection_manager = None
        self.price_manager = PriceManager(self.config.get('buffer_size', 1000))
        self.indicator_engine = IndicatorEngine(self.price_manager)
        
        # UI update queue for thread safety
        self.ui_queue = queue.Queue()
        
        # State
        self.is_monitoring = False
        self.selected_symbols = []
        
        # Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Create UI
        self._create_widgets()
        self._setup_callbacks()
        
        # Start UI update timer
        self._schedule_ui_updates()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file {self.config_file} not found, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "dde_server": "MT4",
            "update_interval": 0.1,
            "buffer_size": 1000,
            "ui_refresh_rate": 500,
            "default_symbols": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD"],
            "indicator_presets": {
                "sma_20": {"type": "SMA", "period": 20},
                "ema_12": {"type": "EMA", "period": 12},
                "rsi_14": {"type": "RSI", "period": 14},
                "macd_standard": {"type": "MACD", "fast_period": 12, "slow_period": 26, "signal_period": 9}
            }
        }
    
    def _create_widgets(self):
        """Create main UI widgets"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel
        left_panel = ttk.Frame(main_paned)
        main_paned.add(left_panel, weight=1)
        
        # Right panel
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=2)
        
        self._create_left_panel(left_panel)
        self._create_right_panel(right_panel)
    
    def _create_left_panel(self, parent):
        """Create left control panel"""
        # Connection section
        connection_frame = ttk.LabelFrame(parent, text="Connection", padding="10")
        connection_frame.pack(fill='x', pady=(0, 10))
        
        # Connection status widget
        self.status_widget = ConnectionStatusWidget(connection_frame)
        self.status_widget.pack(fill='x', pady=(0, 10))
        
        # Connection buttons
        button_frame = ttk.Frame(connection_frame)
        button_frame.pack(fill='x')
        
        self.connect_button = ttk.Button(
            button_frame,
            text="Connect",
            command=self._connect_dde
        )
        self.connect_button.pack(side='left', padx=(0, 5))
        
        self.disconnect_button = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self._disconnect_dde,
            state='disabled'
        )
        self.disconnect_button.pack(side='left')
        
        # Symbol selection section
        symbol_frame = ttk.LabelFrame(parent, text="Symbols", padding="10")
        symbol_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.symbol_widget = SymbolSelectorWidget(
            symbol_frame,
            symbols_list=self.config.get('default_symbols', [])
        )
        self.symbol_widget.pack(fill='both', expand=True)
        
        # Monitoring controls
        monitor_frame = ttk.LabelFrame(parent, text="Monitoring", padding="10")
        monitor_frame.pack(fill='x')
        
        self.start_button = ttk.Button(
            monitor_frame,
            text="Start Monitoring",
            command=self._start_monitoring,
            state='disabled'
        )
        self.start_button.pack(side='left', padx=(0, 5))
        
        self.stop_button = ttk.Button(
            monitor_frame,
            text="Stop Monitoring",
            command=self._stop_monitoring,
            state='disabled'
        )
        self.stop_button.pack(side='left')
    
    def _create_right_panel(self, parent):
        """Create right data panel"""
        # Create notebook for different views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)
        
        # Price data tab
        price_frame = ttk.Frame(self.notebook)
        self.notebook.add(price_frame, text="Live Prices")
        
        self.price_widget = PriceGridWidget(price_frame)
        self.price_widget.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Indicators tab
        indicator_frame = ttk.Frame(self.notebook)
        self.notebook.add(indicator_frame, text="Indicators")
        
        # Split indicators tab into config and display
        indicator_paned = ttk.PanedWindow(indicator_frame, orient='vertical')
        indicator_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Indicator configuration
        config_frame = ttk.Frame(indicator_paned)
        indicator_paned.add(config_frame, weight=1)
        
        self.indicator_panel = IndicatorPanelWidget(config_frame)
        self.indicator_panel.pack(fill='both', expand=True)
        
        # Indicator values display
        values_frame = ttk.Frame(indicator_paned)
        indicator_paned.add(values_frame, weight=1)
        
        self._create_indicator_values_display(values_frame)
        
        # Charts tab
        chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(chart_frame, text="Charts")
        
        self.chart_widget = RealTimeChartWidget(chart_frame)
        self.chart_widget.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Statistics tab
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistics")
        
        self._create_statistics_display(stats_frame)
    
    def _create_indicator_values_display(self, parent):
        """Create indicator values display"""
        ttk.Label(parent, text="Indicator Values", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Treeview for indicator values
        columns = ('Symbol', 'Indicator', 'Value', 'Status', 'Last Update')
        self.indicator_values_tree = ttk.Treeview(parent, columns=columns, show='headings')
        
        for col in columns:
            self.indicator_values_tree.heading(col, text=col)
            self.indicator_values_tree.column(col, width=100)
        
        # Scrollbar
        values_scrollbar = ttk.Scrollbar(parent, orient='vertical', command=self.indicator_values_tree.yview)
        self.indicator_values_tree.config(yscrollcommand=values_scrollbar.set)
        
        self.indicator_values_tree.pack(side='left', fill='both', expand=True)
        values_scrollbar.pack(side='right', fill='y')
    
    def _create_statistics_display(self, parent):
        """Create statistics display"""
        # System statistics
        system_frame = ttk.LabelFrame(parent, text="System Statistics", padding="10")
        system_frame.pack(fill='x', padx=5, pady=5)
        
        self.system_stats_text = tk.Text(system_frame, height=6, state='disabled')
        self.system_stats_text.pack(fill='x')
        
        # Symbol statistics
        symbol_frame = ttk.LabelFrame(parent, text="Symbol Statistics", padding="10")
        symbol_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Symbol stats treeview
        stats_columns = ('Symbol', 'Total Ticks', 'Last Price', 'Min/Max', 'Avg Spread')
        self.symbol_stats_tree = ttk.Treeview(symbol_frame, columns=stats_columns, show='headings')
        
        for col in stats_columns:
            self.symbol_stats_tree.heading(col, text=col)
            self.symbol_stats_tree.column(col, width=100)
        
        stats_scrollbar = ttk.Scrollbar(symbol_frame, orient='vertical', command=self.symbol_stats_tree.yview)
        self.symbol_stats_tree.config(yscrollcommand=stats_scrollbar.set)
        
        self.symbol_stats_tree.pack(side='left', fill='both', expand=True)
        stats_scrollbar.pack(side='right', fill='y')
    
    def _setup_callbacks(self):
        """Setup UI callbacks"""
        # Symbol selector callbacks
        self.symbol_widget.add_callback('add', self._on_symbol_added)
        self.symbol_widget.add_callback('remove', self._on_symbol_removed)
        
        # Indicator panel callbacks
        self.indicator_panel.add_callback('add', self._on_indicator_added)
        self.indicator_panel.add_callback('remove', self._on_indicator_removed)
        self.indicator_panel.add_callback('configure', self._on_indicator_configured)
        
        # Price manager callback (would need to be implemented in price_manager)
        # self.price_manager.add_callback(self._on_price_update)
        
        # Indicator engine callback
        self.indicator_engine.add_update_callback(self._on_indicator_update)
    
    def _connect_dde(self):
        """Connect to MT4 DDE server"""
        try:
            self.dde_client = MT4DDEClient(self.config.get('dde_server', 'MT4'))
            
            if self.dde_client.connect():
                # Setup connection manager
                self.connection_manager = DDEConnectionManager(self.dde_client)
                self.connection_manager.start_auto_reconnect()
                
                # Update UI
                self.status_widget.update_status(True, 0)
                self.connect_button.config(state='disabled')
                self.disconnect_button.config(state='normal')
                self.start_button.config(state='normal')
                
                self.logger.info("Connected to MT4 DDE server")
                messagebox.showinfo("Connection", "Successfully connected to MT4 DDE server")
                
            else:
                messagebox.showerror("Connection Error", "Failed to connect to MT4 DDE server")
                
        except Exception as e:
            self.logger.error(f"DDE connection error: {e}")
            messagebox.showerror("Connection Error", f"Error connecting to MT4: {e}")
    
    def _disconnect_dde(self):
        """Disconnect from MT4 DDE server"""
        try:
            if self.is_monitoring:
                self._stop_monitoring()
            
            if self.connection_manager:
                self.connection_manager.stop_auto_reconnect()
                self.connection_manager = None
            
            if self.dde_client:
                self.dde_client.disconnect()
                self.dde_client = None
            
            # Update UI
            self.status_widget.update_status(False, 0)
            self.connect_button.config(state='normal')
            self.disconnect_button.config(state='disabled')
            self.start_button.config(state='disabled')
            self.stop_button.config(state='disabled')
            
            self.logger.info("Disconnected from MT4 DDE server")
            
        except Exception as e:
            self.logger.error(f"DDE disconnection error: {e}")
            messagebox.showerror("Disconnection Error", f"Error disconnecting: {e}")
    
    def _start_monitoring(self):
        """Start price monitoring"""
        if not self.dde_client or not self.dde_client.is_connected:
            messagebox.showerror("Error", "Not connected to MT4 DDE server")
            return
        
        self.selected_symbols = self.symbol_widget.get_selected_symbols()
        
        if not self.selected_symbols:
            messagebox.showerror("Error", "No symbols selected for monitoring")
            return
        
        try:
            # Add price callback
            self.dde_client.add_price_callback(self._on_price_received)
            
            # Start monitoring
            update_interval = self.config.get('update_interval', 0.1)
            self.dde_client.start_monitoring(self.selected_symbols, update_interval)
            
            # Create default indicators for each symbol
            for symbol in self.selected_symbols:
                create_default_indicator_set(self.indicator_engine, symbol)
            
            self.is_monitoring = True
            
            # Update UI
            self.status_widget.update_status(True, len(self.selected_symbols))
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            self.logger.info(f"Started monitoring {len(self.selected_symbols)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {e}")
            messagebox.showerror("Monitoring Error", f"Error starting monitoring: {e}")
    
    def _stop_monitoring(self):
        """Stop price monitoring"""
        try:
            if self.dde_client:
                self.dde_client.stop_monitoring()
            
            self.is_monitoring = False
            
            # Update UI
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
            self.logger.info("Stopped price monitoring")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")
            messagebox.showerror("Monitoring Error", f"Error stopping monitoring: {e}")
    
    def _on_price_received(self, price_data: Dict):
        """Handle price data received from DDE"""
        # Queue price update for UI thread
        self.ui_queue.put(('price_update', price_data))
    
    def _on_price_update(self, price_data: Dict):
        """Process price update in UI thread"""
        try:
            symbol = price_data['symbol']
            
            # Add to price manager
            self.price_manager.add_price_tick(symbol, price_data)
            
            # Update price grid
            self.price_widget.update_price(
                symbol,
                price_data['bid'],
                price_data['ask'],
                price_data.get('timestamp')
            )
            
            # Update indicators
            mid_price = (price_data['bid'] + price_data['ask']) / 2.0
            indicator_results = self.indicator_engine.update_indicators(symbol, mid_price)
            
            # Update chart
            self.chart_widget.add_price_point(symbol, mid_price, indicator_results)
            
        except Exception as e:
            self.logger.error(f"Error processing price update: {e}")
    
    def _on_indicator_update(self, symbol: str, price: float, results: Dict[str, Any]):
        """Handle indicator update"""
        # Queue indicator update for UI thread
        self.ui_queue.put(('indicator_update', {'symbol': symbol, 'price': price, 'results': results}))
    
    def _on_symbol_added(self, symbol: str):
        """Handle symbol added to selection"""
        self.logger.info(f"Symbol {symbol} added to selection")
    
    def _on_symbol_removed(self, symbol: str):
        """Handle symbol removed from selection"""
        self.logger.info(f"Symbol {symbol} removed from selection")
        
        # Remove indicators for this symbol
        # This would be implemented in the indicator engine
    
    def _on_indicator_added(self, name: str, indicator_type: str, config: Dict):
        """Handle indicator added"""
        selected_symbols = self.symbol_widget.get_selected_symbols()
        
        for symbol in selected_symbols:
            success = self.indicator_engine.add_indicator(symbol, indicator_type, name, config)
            if success:
                self.logger.info(f"Added {indicator_type} indicator '{name}' for {symbol}")
            else:
                self.logger.error(f"Failed to add {indicator_type} indicator '{name}' for {symbol}")
    
    def _on_indicator_removed(self, name: str):
        """Handle indicator removed"""
        selected_symbols = self.symbol_widget.get_selected_symbols()
        
        for symbol in selected_symbols:
            success = self.indicator_engine.remove_indicator(symbol, name)
            if success:
                self.logger.info(f"Removed indicator '{name}' from {symbol}")
    
    def _on_indicator_configured(self, name: str, config: Dict):
        """Handle indicator reconfigured"""
        selected_symbols = self.symbol_widget.get_selected_symbols()
        
        for symbol in selected_symbols:
            success = self.indicator_engine.configure_indicator(symbol, name, config)
            if success:
                self.logger.info(f"Reconfigured indicator '{name}' for {symbol}")
    
    def _schedule_ui_updates(self):
        """Schedule periodic UI updates"""
        self._process_ui_queue()
        
        # Schedule next update
        update_rate = self.config.get('ui_refresh_rate', 500)
        self.after(update_rate, self._schedule_ui_updates)
    
    def _process_ui_queue(self):
        """Process UI update queue"""
        try:
            while not self.ui_queue.empty():
                update_type, data = self.ui_queue.get_nowait()
                
                if update_type == 'price_update':
                    self._on_price_update(data)
                elif update_type == 'indicator_update':
                    self._update_indicator_values_display(data)
                elif update_type == 'statistics_update':
                    self._update_statistics_display()
                
        except queue.Empty:
            pass
        except Exception as e:
            self.logger.error(f"Error processing UI queue: {e}")
        
        # Also update statistics periodically
        self._update_statistics_display()
    
    def _update_indicator_values_display(self, data: Dict):
        """Update indicator values display"""
        symbol = data['symbol']
        results = data['results']
        
        # Clear existing items for this symbol (simplified approach)
        for item in self.indicator_values_tree.get_children():
            item_symbol = self.indicator_values_tree.item(item, 'values')[0]
            if item_symbol == symbol:
                self.indicator_values_tree.delete(item)
        
        # Add updated values
        for indicator_name, value in results.items():
            if isinstance(value, dict):
                # Multi-value indicator
                for key, val in value.items():
                    self.indicator_values_tree.insert('', 'end', values=(
                        symbol,
                        f"{indicator_name}.{key}",
                        f"{val:.5f}" if isinstance(val, (int, float)) else str(val),
                        "Active",
                        datetime.now().strftime("%H:%M:%S")
                    ))
            else:
                # Single-value indicator
                self.indicator_values_tree.insert('', 'end', values=(
                    symbol,
                    indicator_name,
                    f"{value:.5f}" if isinstance(value, (int, float)) else str(value),
                    "Active",
                    datetime.now().strftime("%H:%M:%S")
                ))
    
    def _update_statistics_display(self):
        """Update statistics displays"""
        try:
            # Update system statistics
            engine_stats = self.indicator_engine.get_engine_stats()
            price_stats = self.price_manager.get_system_stats()
            
            stats_text = f"""Engine Statistics:
Symbols: {engine_stats['symbols']}
Total Indicators: {engine_stats['total_indicators']}
Enabled Indicators: {engine_stats['enabled_indicators']}
Updates/sec: {engine_stats['updates_per_second']:.1f}
Runtime: {engine_stats['runtime_seconds']:.0f}s

Price Manager Statistics:
Total Ticks: {price_stats['total_ticks_received']}
Active Symbols: {price_stats['active_symbols']}
Memory Usage: {price_stats['memory_usage_mb']:.1f} MB
"""
            
            self.system_stats_text.config(state='normal')
            self.system_stats_text.delete(1.0, tk.END)
            self.system_stats_text.insert(1.0, stats_text)
            self.system_stats_text.config(state='disabled')
            
            # Update symbol statistics
            for item in self.symbol_stats_tree.get_children():
                self.symbol_stats_tree.delete(item)
            
            for symbol in self.price_manager.get_all_symbols():
                stats = self.price_manager.get_symbol_statistics(symbol)
                
                self.symbol_stats_tree.insert('', 'end', values=(
                    symbol,
                    stats.get('total_ticks', 0),
                    f"{stats.get('last_bid', 0):.5f}",
                    f"{stats.get('min_bid', 0):.5f} / {stats.get('max_bid', 0):.5f}",
                    f"{stats.get('avg_spread', 0):.5f}"
                ))
                
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def save_configuration(self):
        """Save current configuration"""
        try:
            # Export indicator configuration
            indicator_config = self.indicator_engine.export_configuration()
            
            # Save to file
            config_data = {
                'symbols': self.symbol_widget.get_selected_symbols(),
                'indicators': indicator_config,
                'saved_at': datetime.now().isoformat()
            }
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                messagebox.showinfo("Save", f"Configuration saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving configuration: {e}")
    
    def load_configuration(self):
        """Load configuration from file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    config_data = json.load(f)
                
                # Load symbols
                symbols = config_data.get('symbols', [])
                for symbol in symbols:
                    self.symbol_widget._add_symbol()  # This would need adjustment
                
                # Load indicators
                indicator_config = config_data.get('indicators', {})
                self.indicator_engine.import_configuration(indicator_config)
                
                messagebox.showinfo("Load", f"Configuration loaded from {filename}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading configuration: {e}")


# Main application class
class DDEPriceImportApp:
    """Main application wrapper"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MT4 DDE Price Import with Technical Indicators")
        self.root.geometry("1200x800")
        
        # Create main tab
        self.main_tab = DDEPriceImportTab(self.root)
        self.main_tab.pack(fill='both', expand=True)
        
        # Menu bar
        self._create_menu()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Configuration", command=self.main_tab.save_configuration)
        file_menu.add_command(label="Load Configuration", command=self.main_tab.load_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "MT4 DDE Price Import with Technical Indicators\n\n"
            "Real-time price data import from MetaTrader 4\n"
            "with comprehensive technical analysis indicators.\n\n"
            "Features:\n"
            "• Real-time DDE price feeds\n"
            "• Multiple technical indicators\n"
            "• Real-time charts\n"
            "• Performance statistics\n"
            "• Configuration save/load"
        )
    
    def _on_closing(self):
        """Handle application close"""
        try:
            # Disconnect DDE if connected
            if self.main_tab.dde_client:
                self.main_tab._disconnect_dde()
            
            self.root.destroy()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = DDEPriceImportApp()
    app.run()