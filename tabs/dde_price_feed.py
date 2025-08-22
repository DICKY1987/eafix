"""
DDE Price Feed Tab - Real-time MT4 price data via DDE
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dde_client import MT4DDEClient, DDEConnectionManager
    from price_manager import PriceManager
    from indicators.base_indicator import BaseIndicator
except ImportError as e:
    logging.warning(f"DDE modules not available: {e}")
    MT4DDEClient = None
    DDEConnectionManager = None
    PriceManager = None

logger = logging.getLogger(__name__)

class DDEPriceFeedTab:
    """DDE Price Feed tab for real-time MT4 price monitoring"""
    
    def __init__(self, parent_notebook: ttk.Notebook):
        self.parent_notebook = parent_notebook
        self.frame = None
        
        # DDE components
        self.dde_client = None
        self.connection_manager = None
        self.price_manager = None
        
        # UI components
        self.connection_frame = None
        self.symbol_frame = None
        self.price_tree = None
        self.status_label = None
        
        # Data
        self.monitored_symbols = set()
        self.price_data = {}
        self.is_connected = False
        self.is_monitoring = False
        
        # Update thread
        self.update_thread = None
        self.running = False
        
        self.setup_ui()
        logger.info("DDE Price Feed tab initialized")
    
    def setup_ui(self):
        """Setup the DDE tab user interface"""
        # Create main frame
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="DDE Price Feed")
        
        # Title
        title_label = tk.Label(self.frame, text="MT4 DDE Price Feed", 
                              font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        # Connection control frame
        self._create_connection_frame()
        
        # Symbol management frame
        self._create_symbol_frame()
        
        # Price display frame
        self._create_price_display()
        
        # Status bar
        self._create_status_bar()
        
        logger.info("DDE Price Feed UI setup complete")
    
    def _create_connection_frame(self):
        """Create DDE connection controls"""
        self.connection_frame = ttk.LabelFrame(self.frame, text="DDE Connection")
        self.connection_frame.pack(fill='x', padx=10, pady=5)
        
        # Connection controls
        controls_frame = tk.Frame(self.connection_frame)
        controls_frame.pack(fill='x', padx=5, pady=5)
        
        # Server name entry
        tk.Label(controls_frame, text="MT4 Server:").pack(side='left')
        self.server_entry = tk.Entry(controls_frame, width=15)
        self.server_entry.insert(0, "MT4")
        self.server_entry.pack(side='left', padx=(5, 10))
        
        # Connect button
        self.connect_btn = ttk.Button(controls_frame, text="Connect", 
                                     command=self._toggle_connection)
        self.connect_btn.pack(side='left', padx=5)
        
        # Connection status
        self.conn_status_label = tk.Label(controls_frame, text="Disconnected", 
                                         fg='red', font=('Arial', 9, 'bold'))
        self.conn_status_label.pack(side='left', padx=10)
    
    def _create_symbol_frame(self):
        """Create symbol management controls"""
        self.symbol_frame = ttk.LabelFrame(self.frame, text="Symbol Management")
        self.symbol_frame.pack(fill='x', padx=10, pady=5)
        
        # Symbol controls
        symbol_controls = tk.Frame(self.symbol_frame)
        symbol_controls.pack(fill='x', padx=5, pady=5)
        
        # Symbol entry
        tk.Label(symbol_controls, text="Symbol:").pack(side='left')
        self.symbol_entry = tk.Entry(symbol_controls, width=12)
        self.symbol_entry.pack(side='left', padx=(5, 10))
        self.symbol_entry.bind('<Return>', lambda e: self._add_symbol())
        
        # Add/Remove buttons
        ttk.Button(symbol_controls, text="Add Symbol", 
                  command=self._add_symbol).pack(side='left', padx=2)
        ttk.Button(symbol_controls, text="Remove Symbol", 
                  command=self._remove_symbol).pack(side='left', padx=2)
        
        # Monitor toggle
        self.monitor_btn = ttk.Button(symbol_controls, text="Start Monitoring", 
                                     command=self._toggle_monitoring)
        self.monitor_btn.pack(side='left', padx=10)
        
        # Quick add common symbols
        common_frame = tk.Frame(self.symbol_frame)
        common_frame.pack(fill='x', padx=5, pady=2)
        
        tk.Label(common_frame, text="Quick Add:").pack(side='left')
        common_symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD"]
        for symbol in common_symbols:
            btn = ttk.Button(common_frame, text=symbol, width=8,
                           command=lambda s=symbol: self._quick_add_symbol(s))
            btn.pack(side='left', padx=2)
    
    def _create_price_display(self):
        """Create price data display table"""
        price_frame = ttk.LabelFrame(self.frame, text="Live Price Data")
        price_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create treeview for price data
        columns = ("Symbol", "Bid", "Ask", "Spread", "Last Update", "Status")
        self.price_tree = ttk.Treeview(price_frame, columns=columns, show='headings', height=12)
        
        # Configure columns
        col_widths = {"Symbol": 80, "Bid": 80, "Ask": 80, "Spread": 60, "Last Update": 120, "Status": 80}
        for col in columns:
            self.price_tree.heading(col, text=col)
            self.price_tree.column(col, width=col_widths.get(col, 80))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(price_frame, orient='vertical', command=self.price_tree.yview)
        h_scrollbar = ttk.Scrollbar(price_frame, orient='horizontal', command=self.price_tree.xview)
        self.price_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack components
        self.price_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
    
    def _create_status_bar(self):
        """Create status information bar"""
        status_frame = tk.Frame(self.frame, relief='sunken', bd=1)
        status_frame.pack(side='bottom', fill='x', padx=10, pady=2)
        
        self.status_label = tk.Label(status_frame, text="Ready - DDE not connected", anchor='w')
        self.status_label.pack(side='left', padx=5)
        
        self.stats_label = tk.Label(status_frame, text="Symbols: 0 | Updates: 0", anchor='e')
        self.stats_label.pack(side='right', padx=5)
    
    def _toggle_connection(self):
        """Toggle DDE connection"""
        if not MT4DDEClient:
            messagebox.showerror("Error", "DDE modules not available. Install pywin32 and restart.")
            return
            
        try:
            if not self.is_connected:
                # Connect
                server_name = self.server_entry.get().strip() or "MT4"
                self.dde_client = MT4DDEClient(server_name)
                
                if self.dde_client.connect():
                    self.is_connected = True
                    self.connect_btn.config(text="Disconnect")
                    self.conn_status_label.config(text="Connected", fg='green')
                    self.status_label.config(text=f"Connected to {server_name} DDE server")
                    logger.info(f"Connected to {server_name} DDE server")
                else:
                    messagebox.showerror("Connection Error", "Failed to connect to MT4 DDE server")
            else:
                # Disconnect
                if self.dde_client:
                    self.dde_client.disconnect()
                    self.dde_client = None
                
                self.is_connected = False
                self.is_monitoring = False
                self.connect_btn.config(text="Connect")
                self.monitor_btn.config(text="Start Monitoring")
                self.conn_status_label.config(text="Disconnected", fg='red')
                self.status_label.config(text="Disconnected from DDE server")
                logger.info("Disconnected from DDE server")
                
        except Exception as e:
            logger.error(f"Connection toggle failed: {e}")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def _add_symbol(self):
        """Add symbol to monitoring list"""
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return
            
        if symbol not in self.monitored_symbols:
            self.monitored_symbols.add(symbol)
            self._add_symbol_to_tree(symbol)
            self.symbol_entry.delete(0, 'end')
            
            # Subscribe if connected and monitoring
            if self.is_connected and self.is_monitoring and self.dde_client:
                try:
                    self.dde_client.subscribe_symbol(symbol, self._price_callback)
                    logger.info(f"Subscribed to {symbol}")
                except Exception as e:
                    logger.error(f"Failed to subscribe to {symbol}: {e}")
        else:
            messagebox.showwarning("Duplicate", f"Symbol {symbol} is already being monitored")
    
    def _quick_add_symbol(self, symbol: str):
        """Quick add symbol from predefined list"""
        self.symbol_entry.delete(0, 'end')
        self.symbol_entry.insert(0, symbol)
        self._add_symbol()
    
    def _remove_symbol(self):
        """Remove selected symbol from monitoring"""
        selection = self.price_tree.selection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a symbol to remove")
            return
            
        item = selection[0]
        symbol = self.price_tree.item(item)['values'][0]
        
        # Unsubscribe if connected
        if self.is_connected and self.dde_client:
            try:
                self.dde_client.unsubscribe_symbol(symbol)
                logger.info(f"Unsubscribed from {symbol}")
            except Exception as e:
                logger.error(f"Failed to unsubscribe from {symbol}: {e}")
        
        # Remove from tree and set
        self.price_tree.delete(item)
        self.monitored_symbols.discard(symbol)
        if symbol in self.price_data:
            del self.price_data[symbol]
    
    def _toggle_monitoring(self):
        """Toggle price monitoring"""
        if not self.is_connected:
            messagebox.showerror("Error", "Must be connected to DDE server first")
            return
            
        try:
            if not self.is_monitoring:
                # Start monitoring
                if self.monitored_symbols and self.dde_client:
                    for symbol in self.monitored_symbols:
                        self.dde_client.subscribe_symbol(symbol, self._price_callback)
                    
                    self.dde_client.start_monitoring()
                    self.is_monitoring = True
                    self.monitor_btn.config(text="Stop Monitoring")
                    self.status_label.config(text=f"Monitoring {len(self.monitored_symbols)} symbols")
                    logger.info(f"Started monitoring {len(self.monitored_symbols)} symbols")
                else:
                    messagebox.showwarning("No Symbols", "Add symbols to monitor first")
            else:
                # Stop monitoring
                if self.dde_client:
                    self.dde_client.stop_monitoring()
                
                self.is_monitoring = False
                self.monitor_btn.config(text="Start Monitoring")
                self.status_label.config(text="Monitoring stopped")
                logger.info("Stopped monitoring")
                
        except Exception as e:
            logger.error(f"Monitoring toggle failed: {e}")
            messagebox.showerror("Error", f"Monitoring error: {str(e)}")
    
    def _add_symbol_to_tree(self, symbol: str):
        """Add symbol row to price tree"""
        self.price_tree.insert('', 'end', values=(symbol, "--", "--", "--", "Never", "Waiting"))
        self.price_data[symbol] = {
            'bid': None,
            'ask': None,
            'last_update': None
        }
    
    def _price_callback(self, symbol: str, bid: float, ask: float):
        """Callback for price updates from DDE"""
        try:
            # Update internal data
            self.price_data[symbol] = {
                'bid': bid,
                'ask': ask,
                'last_update': datetime.now()
            }
            
            # Schedule UI update on main thread
            self.frame.after(0, lambda: self._update_price_display(symbol))
            
        except Exception as e:
            logger.error(f"Price callback error for {symbol}: {e}")
    
    def _update_price_display(self, symbol: str):
        """Update price display for specific symbol"""
        try:
            if symbol not in self.price_data:
                return
                
            data = self.price_data[symbol]
            bid = data['bid']
            ask = data['ask']
            last_update = data['last_update']
            
            if bid is None or ask is None:
                return
            
            # Calculate spread
            spread = ask - bid
            
            # Format values
            bid_str = f"{bid:.5f}"
            ask_str = f"{ask:.5f}"
            spread_str = f"{spread:.5f}"
            time_str = last_update.strftime("%H:%M:%S") if last_update else "Never"
            
            # Find and update tree item
            for item in self.price_tree.get_children():
                if self.price_tree.item(item)['values'][0] == symbol:
                    self.price_tree.item(item, values=(
                        symbol, bid_str, ask_str, spread_str, time_str, "Live"
                    ))
                    break
                    
        except Exception as e:
            logger.error(f"Failed to update price display for {symbol}: {e}")
    
    def _update_stats(self):
        """Update statistics display"""
        try:
            symbol_count = len(self.monitored_symbols)
            update_count = sum(1 for data in self.price_data.values() 
                             if data['last_update'] is not None)
            
            self.stats_label.config(text=f"Symbols: {symbol_count} | Live: {update_count}")
            
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")
    
    def refresh_data(self):
        """Refresh tab data - called by main controller"""
        try:
            if self.is_connected and self.dde_client:
                # Update connection status
                connection_ok = self.dde_client.is_connected
                if not connection_ok and self.is_connected:
                    # Connection lost
                    self.is_connected = False
                    self.is_monitoring = False
                    self.connect_btn.config(text="Connect")
                    self.monitor_btn.config(text="Start Monitoring")
                    self.conn_status_label.config(text="Connection Lost", fg='orange')
                    self.status_label.config(text="Connection to MT4 lost")
            
            # Update statistics
            self._update_stats()
            
        except Exception as e:
            logger.error(f"Failed to refresh DDE data: {e}")
    
    def cleanup(self):
        """Cleanup resources when tab is closed"""
        try:
            self.running = False
            
            if self.is_monitoring and self.dde_client:
                self.dde_client.stop_monitoring()
            
            if self.is_connected and self.dde_client:
                self.dde_client.disconnect()
            
            logger.info("DDE Price Feed tab cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current tab status"""
        return {
            'connected': self.is_connected,
            'monitoring': self.is_monitoring,
            'symbol_count': len(self.monitored_symbols),
            'live_symbols': len([s for s in self.price_data.values() if s['last_update']]),
            'last_update': max([s['last_update'] for s in self.price_data.values() 
                               if s['last_update']], default=None)
        }

# Fallback DDE tab for when modules aren't available
class DDEPriceFeedTabFallback:
    """Fallback DDE tab when DDE modules aren't available"""
    
    def __init__(self, parent_notebook: ttk.Notebook):
        self.parent_notebook = parent_notebook
        self.frame = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup fallback UI"""
        self.frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.frame, text="DDE Price Feed")
        
        # Message frame
        msg_frame = tk.Frame(self.frame)
        msg_frame.pack(expand=True, fill='both')
        
        # Title
        title_label = tk.Label(msg_frame, text="DDE Price Feed", 
                              font=('Arial', 14, 'bold'))
        title_label.pack(pady=20)
        
        # Info message
        info_text = """DDE functionality requires additional modules.
        
To enable DDE price feeds:
1. Install required modules: pip install pywin32
2. Enable DDE in MT4: Tools → Options → Server → Enable DDE server
3. Restart this application

Current Status: DDE modules not available"""
        
        info_label = tk.Label(msg_frame, text=info_text, justify='center', 
                             wraplength=400, font=('Arial', 10))
        info_label.pack(pady=20)
        
        # Install button
        install_btn = ttk.Button(msg_frame, text="Install Required Modules", 
                                command=self._show_install_instructions)
        install_btn.pack(pady=10)
    
    def _show_install_instructions(self):
        """Show installation instructions"""
        instructions = """To install DDE support:

1. Open command prompt as administrator
2. Run: pip install pywin32
3. Restart this application
4. Enable DDE in MT4: Tools → Options → Server → Enable DDE server

Note: DDE requires Windows and MetaTrader 4"""
        
        messagebox.showinfo("Installation Instructions", instructions)
    
    def refresh_data(self):
        """Placeholder refresh method"""
        pass
    
    def cleanup(self):
        """Placeholder cleanup method"""
        pass
    
    def get_status(self):
        """Return fallback status"""
        return {'available': False, 'reason': 'DDE modules not installed'}

def create_dde_tab(parent_notebook: ttk.Notebook):
    """Factory function to create appropriate DDE tab"""
    if MT4DDEClient is not None:
        return DDEPriceFeedTab(parent_notebook)
    else:
        return DDEPriceFeedTabFallback(parent_notebook)