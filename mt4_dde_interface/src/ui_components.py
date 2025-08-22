"""
UI Components for DDE Price Import Tab
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


class ConnectionStatusWidget(ttk.Frame):
    """Widget showing DDE connection status"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.connection_status = "Disconnected"
        self.symbol_count = 0
        self.last_update = None
        
        self._create_widgets()
        self._update_display()
    
    def _create_widgets(self):
        """Create status display widgets"""
        # Status indicator
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(self.status_frame, text="DDE Status:").pack(side='left')
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text=self.connection_status,
            foreground="red"
        )
        self.status_label.pack(side='left', padx=(5, 0))
        
        self.status_indicator = tk.Canvas(
            self.status_frame, 
            width=15, 
            height=15, 
            highlightthickness=0
        )
        self.status_indicator.pack(side='left', padx=(5, 0))
        
        # Symbol count
        self.symbol_frame = ttk.Frame(self)
        self.symbol_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(self.symbol_frame, text="Symbols:").pack(side='left')
        self.symbol_label = ttk.Label(self.symbol_frame, text="0")
        self.symbol_label.pack(side='left', padx=(5, 0))
        
        # Last update
        self.update_frame = ttk.Frame(self)
        self.update_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(self.update_frame, text="Last Update:").pack(side='left')
        self.update_label = ttk.Label(self.update_frame, text="Never")
        self.update_label.pack(side='left', padx=(5, 0))
    
    def update_status(self, connected: bool, symbol_count: int = 0):
        """Update connection status"""
        self.connection_status = "Connected" if connected else "Disconnected"
        self.symbol_count = symbol_count
        self.last_update = datetime.now()
        
        self._update_display()
    
    def _update_display(self):
        """Update visual display"""
        # Update status text and color
        if self.connection_status == "Connected":
            self.status_label.config(text=self.connection_status, foreground="green")
            self.status_indicator.delete("all")
            self.status_indicator.create_oval(2, 2, 13, 13, fill="green", outline="darkgreen")
        else:
            self.status_label.config(text=self.connection_status, foreground="red")
            self.status_indicator.delete("all")
            self.status_indicator.create_oval(2, 2, 13, 13, fill="red", outline="darkred")
        
        # Update symbol count
        self.symbol_label.config(text=str(self.symbol_count))
        
        # Update last update time
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
        else:
            time_str = "Never"
        self.update_label.config(text=time_str)


class SymbolSelectorWidget(ttk.Frame):
    """Widget for selecting and managing symbols"""
    
    def __init__(self, parent, symbols_list: List[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.symbols_list = symbols_list or []
        self.selected_symbols = set()
        self.callbacks = {'add': [], 'remove': []}
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create symbol selector widgets"""
        # Title
        title_label = ttk.Label(self, text="Symbol Selection", font=('Arial', 10, 'bold'))
        title_label.pack(anchor='w', pady=(0, 5))
        
        # Symbol input frame
        input_frame = ttk.Frame(self)
        input_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(input_frame, text="Symbol:").pack(side='left')
        
        self.symbol_var = tk.StringVar()
        self.symbol_combo = ttk.Combobox(
            input_frame,
            textvariable=self.symbol_var,
            values=self.symbols_list,
            state='normal'
        )
        self.symbol_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        self.add_button = ttk.Button(
            input_frame,
            text="Add",
            command=self._add_symbol,
            width=8
        )
        self.add_button.pack(side='right', padx=(5, 0))
        
        # Selected symbols listbox
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True)
        
        ttk.Label(list_frame, text="Selected Symbols:").pack(anchor='w')
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill='both', expand=True)
        
        self.symbols_listbox = tk.Listbox(listbox_frame, height=6)
        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.symbols_listbox.yview)
        
        self.symbols_listbox.config(yscrollcommand=scrollbar.set)
        
        self.symbols_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Remove button
        self.remove_button = ttk.Button(
            list_frame,
            text="Remove Selected",
            command=self._remove_selected,
            state='disabled'
        )
        self.remove_button.pack(pady=(5, 0))
        
        # Bind events
        self.symbols_listbox.bind('<<ListboxSelect>>', self._on_select)
        self.symbol_combo.bind('<Return>', lambda e: self._add_symbol())
    
    def _add_symbol(self):
        """Add symbol to selected list"""
        symbol = self.symbol_var.get().strip().upper()
        if symbol and symbol not in self.selected_symbols:
            self.selected_symbols.add(symbol)
            self.symbols_listbox.insert('end', symbol)
            self.symbol_var.set('')
            
            # Notify callbacks
            for callback in self.callbacks['add']:
                try:
                    callback(symbol)
                except Exception as e:
                    print(f"Error in add callback: {e}")
    
    def _remove_selected(self):
        """Remove selected symbol from list"""
        selection = self.symbols_listbox.curselection()
        if selection:
            index = selection[0]
            symbol = self.symbols_listbox.get(index)
            
            self.symbols_listbox.delete(index)
            self.selected_symbols.discard(symbol)
            self.remove_button.config(state='disabled')
            
            # Notify callbacks
            for callback in self.callbacks['remove']:
                try:
                    callback(symbol)
                except Exception as e:
                    print(f"Error in remove callback: {e}")
    
    def _on_select(self, event):
        """Handle listbox selection"""
        selection = self.symbols_listbox.curselection()
        self.remove_button.config(state='normal' if selection else 'disabled')
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for symbol events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def get_selected_symbols(self) -> List[str]:
        """Get list of selected symbols"""
        return list(self.selected_symbols)
    
    def clear_symbols(self):
        """Clear all selected symbols"""
        self.symbols_listbox.delete(0, 'end')
        self.selected_symbols.clear()


class PriceGridWidget(ttk.Frame):
    """Widget displaying real-time price data in a grid"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.price_data = {}  # symbol -> price_info
        self.sort_column = None
        self.sort_reverse = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create price grid widgets"""
        # Title
        title_label = ttk.Label(self, text="Real-Time Prices", font=('Arial', 10, 'bold'))
        title_label.pack(anchor='w', pady=(0, 5))
        
        # Treeview for price data
        columns = ('Symbol', 'Bid', 'Ask', 'Spread', 'Change', 'Time')
        
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.tree.heading('Symbol', text='Symbol', command=lambda: self._sort_by_column('Symbol'))
        self.tree.heading('Bid', text='Bid', command=lambda: self._sort_by_column('Bid'))
        self.tree.heading('Ask', text='Ask', command=lambda: self._sort_by_column('Ask'))
        self.tree.heading('Spread', text='Spread', command=lambda: self._sort_by_column('Spread'))
        self.tree.heading('Change', text='Change', command=lambda: self._sort_by_column('Change'))
        self.tree.heading('Time', text='Time', command=lambda: self._sort_by_column('Time'))
        
        # Configure column widths
        self.tree.column('Symbol', width=80)
        self.tree.column('Bid', width=80)
        self.tree.column('Ask', width=80)
        self.tree.column('Spread', width=60)
        self.tree.column('Change', width=80)
        self.tree.column('Time', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.config(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def update_price(self, symbol: str, bid: float, ask: float, timestamp: datetime = None):
        """Update price data for symbol"""
        if timestamp is None:
            timestamp = datetime.now()
        
        spread = ask - bid
        
        # Calculate change from previous price
        change = 0.0
        change_color = 'black'
        if symbol in self.price_data:
            prev_mid = (self.price_data[symbol]['bid'] + self.price_data[symbol]['ask']) / 2
            current_mid = (bid + ask) / 2
            change = current_mid - prev_mid
            change_color = 'green' if change > 0 else 'red' if change < 0 else 'black'
        
        # Store price data
        self.price_data[symbol] = {
            'bid': bid,
            'ask': ask,
            'spread': spread,
            'change': change,
            'timestamp': timestamp,
            'change_color': change_color
        }
        
        # Update treeview
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the price display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add updated data
        for symbol, data in self.price_data.items():
            change_text = f"{data['change']:+.5f}" if data['change'] != 0 else "0.00000"
            time_text = data['timestamp'].strftime("%H:%M:%S")
            
            item = self.tree.insert('', 'end', values=(
                symbol,
                f"{data['bid']:.5f}",
                f"{data['ask']:.5f}",
                f"{data['spread']:.5f}",
                change_text,
                time_text
            ))
            
            # Color coding for change
            if data['change_color'] != 'black':
                self.tree.set(item, 'Change', change_text)
    
    def _sort_by_column(self, column: str):
        """Sort data by column"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Sort logic would be implemented here
        # For now, just refresh display
        self._refresh_display()


class IndicatorConfigWidget(tk.Toplevel):
    """Dialog for configuring indicator parameters"""
    
    def __init__(self, parent, indicator_type: str, existing_config: Dict = None):
        super().__init__(parent)
        
        self.indicator_type = indicator_type
        self.existing_config = existing_config or {}
        self.result = None
        
        self.title(f"Configure {indicator_type}")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._center_window()
    
    def _create_widgets(self):
        """Create configuration widgets"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text=f"Configure {self.indicator_type}",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Configuration fields (simplified - real implementation would be dynamic)
        self.config_vars = {}
        
        if self.indicator_type in ['SMA', 'EMA', 'WMA']:
            self._add_config_field(main_frame, "Period", "period", "int", 20)
        elif self.indicator_type == 'RSI':
            self._add_config_field(main_frame, "Period", "period", "int", 14)
        elif self.indicator_type == 'MACD':
            self._add_config_field(main_frame, "Fast Period", "fast_period", "int", 12)
            self._add_config_field(main_frame, "Slow Period", "slow_period", "int", 26)
            self._add_config_field(main_frame, "Signal Period", "signal_period", "int", 9)
        elif self.indicator_type == 'BollingerBands':
            self._add_config_field(main_frame, "Period", "period", "int", 20)
            self._add_config_field(main_frame, "Standard Deviations", "std_dev", "float", 2.0)
        elif self.indicator_type == 'ATR':
            self._add_config_field(main_frame, "Period", "period", "int", 14)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0), fill='x')
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side='right', padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._ok
        ).pack(side='right')
    
    def _add_config_field(self, parent, label: str, key: str, field_type: str, default_value):
        """Add configuration field"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        
        ttk.Label(frame, text=f"{label}:").pack(side='left')
        
        var = tk.StringVar(value=str(self.existing_config.get(key, default_value)))
        entry = ttk.Entry(frame, textvariable=var, width=15)
        entry.pack(side='right')
        
        self.config_vars[key] = (var, field_type)
    
    def _center_window(self):
        """Center window on parent"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _ok(self):
        """OK button handler"""
        try:
            config = {}
            for key, (var, field_type) in self.config_vars.items():
                value = var.get()
                if field_type == 'int':
                    config[key] = int(value)
                elif field_type == 'float':
                    config[key] = float(value)
                else:
                    config[key] = value
            
            self.result = config
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input values:\n{e}")
    
    def _cancel(self):
        """Cancel button handler"""
        self.result = None
        self.destroy()


class RealTimeChartWidget(ttk.Frame):
    """Widget for displaying real-time price and indicator charts"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.price_history = {}  # symbol -> list of prices
        self.indicator_history = {}  # symbol -> indicator_name -> list of values
        self.max_points = 200
        self.current_symbol = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create chart widgets"""
        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(control_frame, text="Chart Symbol:").pack(side='left')
        
        self.symbol_var = tk.StringVar()
        self.symbol_combo = ttk.Combobox(
            control_frame,
            textvariable=self.symbol_var,
            values=[],
            state='readonly',
            width=15
        )
        self.symbol_combo.pack(side='left', padx=(5, 0))
        self.symbol_combo.bind('<<ComboboxSelected>>', self._on_symbol_change)
        
        # Chart frame
        self.figure = Figure(figsize=(8, 4), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Initialize empty plot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Select a symbol to view chart")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def add_price_point(self, symbol: str, price: float, indicators: Dict[str, Any] = None):
        """Add price and indicator data point"""
        # Add price data
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.indicator_history[symbol] = {}
            
            # Update symbol combo
            symbols = list(self.price_history.keys())
            self.symbol_combo.config(values=symbols)
            if not self.current_symbol:
                self.current_symbol = symbol
                self.symbol_var.set(symbol)
        
        # Maintain max points
        if len(self.price_history[symbol]) >= self.max_points:
            self.price_history[symbol].pop(0)
        
        self.price_history[symbol].append(price)
        
        # Add indicator data
        if indicators:
            for ind_name, ind_value in indicators.items():
                if isinstance(ind_value, (int, float)):  # Simple numeric indicators
                    if ind_name not in self.indicator_history[symbol]:
                        self.indicator_history[symbol][ind_name] = []
                    
                    if len(self.indicator_history[symbol][ind_name]) >= self.max_points:
                        self.indicator_history[symbol][ind_name].pop(0)
                    
                    self.indicator_history[symbol][ind_name].append(ind_value)
        
        # Update chart if this is the current symbol
        if symbol == self.current_symbol:
            self._update_chart()
    
    def _on_symbol_change(self, event):
        """Handle symbol selection change"""
        self.current_symbol = self.symbol_var.get()
        self._update_chart()
    
    def _update_chart(self):
        """Update the chart display"""
        if not self.current_symbol or self.current_symbol not in self.price_history:
            return
        
        self.ax.clear()
        
        prices = self.price_history[self.current_symbol]
        if not prices:
            self.ax.set_title(f"{self.current_symbol} - No Data")
            self.canvas.draw()
            return
        
        x = list(range(len(prices)))
        
        # Plot price line
        self.ax.plot(x, prices, label='Price', color='blue', linewidth=1.5)
        
        # Plot indicators (simplified - show up to 3 indicators)
        indicators = self.indicator_history.get(self.current_symbol, {})
        colors = ['red', 'green', 'orange', 'purple', 'brown']
        color_idx = 0
        
        for ind_name, values in list(indicators.items())[:3]:  # Limit to 3 indicators
            if len(values) == len(prices):  # Ensure same length
                self.ax.plot(x, values, label=ind_name, color=colors[color_idx % len(colors)], alpha=0.7)
                color_idx += 1
        
        self.ax.set_title(f"{self.current_symbol} - Real-Time Chart")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Price")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Auto-scale
        self.ax.relim()
        self.ax.autoscale_view()
        
        self.canvas.draw()


class IndicatorPanelWidget(ttk.Frame):
    """Panel for managing indicators"""
    
    def __init__(self, parent, available_indicators: List[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.available_indicators = available_indicators or [
            'SMA', 'EMA', 'WMA', 'RSI', 'MACD', 'BollingerBands', 'ATR'
        ]
        self.active_indicators = {}  # indicator_name -> config
        self.callbacks = {'add': [], 'remove': [], 'configure': []}
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create indicator panel widgets"""
        # Title
        title_label = ttk.Label(self, text="Technical Indicators", font=('Arial', 10, 'bold'))
        title_label.pack(anchor='w', pady=(0, 5))
        
        # Add indicator frame
        add_frame = ttk.Frame(self)
        add_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(add_frame, text="Add Indicator:").pack(side='left')
        
        self.indicator_var = tk.StringVar()
        indicator_combo = ttk.Combobox(
            add_frame,
            textvariable=self.indicator_var,
            values=self.available_indicators,
            state='readonly'
        )
        indicator_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        add_button = ttk.Button(
            add_frame,
            text="Add",
            command=self._add_indicator
        )
        add_button.pack(side='right', padx=(5, 0))
        
        # Active indicators list
        ttk.Label(self, text="Active Indicators:").pack(anchor='w')
        
        # Treeview for active indicators
        columns = ('Name', 'Type', 'Config', 'Status')
        self.indicators_tree = ttk.Treeview(self, columns=columns, show='headings', height=8)
        
        self.indicators_tree.heading('Name', text='Name')
        self.indicators_tree.heading('Type', text='Type')
        self.indicators_tree.heading('Config', text='Configuration')
        self.indicators_tree.heading('Status', text='Status')
        
        self.indicators_tree.column('Name', width=100)
        self.indicators_tree.column('Type', width=80)
        self.indicators_tree.column('Config', width=150)
        self.indicators_tree.column('Status', width=80)
        
        # Scrollbar for indicators tree
        indicators_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.indicators_tree.yview)
        self.indicators_tree.config(yscrollcommand=indicators_scrollbar.set)
        
        self.indicators_tree.pack(side='left', fill='both', expand=True)
        indicators_scrollbar.pack(side='right', fill='y')
        
        # Context menu for indicators
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Configure", command=self._configure_indicator)
        self.context_menu.add_command(label="Remove", command=self._remove_indicator)
        
        self.indicators_tree.bind("<Button-3>", self._show_context_menu)  # Right-click
    
    def _add_indicator(self):
        """Add new indicator"""
        indicator_type = self.indicator_var.get()
        if not indicator_type:
            return
        
        # Open configuration dialog
        config_dialog = IndicatorConfigWidget(self.winfo_toplevel(), indicator_type)
        self.wait_window(config_dialog)
        
        if config_dialog.result:
            # Generate unique name
            base_name = indicator_type
            counter = 1
            name = base_name
            while name in self.active_indicators:
                name = f"{base_name}_{counter}"
                counter += 1
            
            # Add to active indicators
            self.active_indicators[name] = {
                'type': indicator_type,
                'config': config_dialog.result,
                'status': 'Active'
            }
            
            self._refresh_indicators_display()
            
            # Notify callbacks
            for callback in self.callbacks['add']:
                try:
                    callback(name, indicator_type, config_dialog.result)
                except Exception as e:
                    print(f"Error in add indicator callback: {e}")
    
    def _configure_indicator(self):
        """Configure selected indicator"""
        selection = self.indicators_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        name = self.indicators_tree.item(item, 'values')[0]
        
        if name in self.active_indicators:
            indicator_info = self.active_indicators[name]
            
            config_dialog = IndicatorConfigWidget(
                self.winfo_toplevel(),
                indicator_info['type'],
                indicator_info['config']
            )
            self.wait_window(config_dialog)
            
            if config_dialog.result:
                # Update configuration
                self.active_indicators[name]['config'] = config_dialog.result
                self._refresh_indicators_display()
                
                # Notify callbacks
                for callback in self.callbacks['configure']:
                    try:
                        callback(name, config_dialog.result)
                    except Exception as e:
                        print(f"Error in configure indicator callback: {e}")
    
    def _remove_indicator(self):
        """Remove selected indicator"""
        selection = self.indicators_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        name = self.indicators_tree.item(item, 'values')[0]
        
        if name in self.active_indicators:
            result = messagebox.askyesno(
                "Remove Indicator",
                f"Are you sure you want to remove indicator '{name}'?"
            )
            
            if result:
                del self.active_indicators[name]
                self._refresh_indicators_display()
                
                # Notify callbacks
                for callback in self.callbacks['remove']:
                    try:
                        callback(name)
                    except Exception as e:
                        print(f"Error in remove indicator callback: {e}")
    
    def _show_context_menu(self, event):
        """Show context menu for indicators"""
        item = self.indicators_tree.identify_row(event.y)
        if item:
            self.indicators_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _refresh_indicators_display(self):
        """Refresh the indicators display"""
        # Clear existing items
        for item in self.indicators_tree.get_children():
            self.indicators_tree.delete(item)
        
        # Add current indicators
        for name, info in self.active_indicators.items():
            config_str = ", ".join(f"{k}={v}" for k, v in info['config'].items())
            
            self.indicators_tree.insert('', 'end', values=(
                name,
                info['type'],
                config_str,
                info['status']
            ))
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for indicator events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def update_indicator_status(self, name: str, status: str):
        """Update indicator status"""
        if name in self.active_indicators:
            self.active_indicators[name]['status'] = status
            self._refresh_indicators_display()


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("UI Components Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Test ConnectionStatusWidget
    status_frame = ttk.Frame(notebook)
    notebook.add(status_frame, text="Status")
    
    status_widget = ConnectionStatusWidget(status_frame)
    status_widget.pack(pady=10)
    
    # Test buttons to change status
    ttk.Button(
        status_frame,
        text="Connect",
        command=lambda: status_widget.update_status(True, 5)
    ).pack(pady=5)
    
    ttk.Button(
        status_frame,
        text="Disconnect",
        command=lambda: status_widget.update_status(False, 0)
    ).pack(pady=5)
    
    # Test SymbolSelectorWidget
    symbol_frame = ttk.Frame(notebook)
    notebook.add(symbol_frame, text="Symbols")
    
    symbol_widget = SymbolSelectorWidget(
        symbol_frame,
        symbols_list=['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
    )
    symbol_widget.pack(fill='both', expand=True, pady=10)
    
    # Test PriceGridWidget
    price_frame = ttk.Frame(notebook)
    notebook.add(price_frame, text="Prices")
    
    price_widget = PriceGridWidget(price_frame)
    price_widget.pack(fill='both', expand=True, pady=10)
    
    # Add some test data
    import random
    def update_prices():
        for symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
            bid = 1.1000 + random.uniform(-0.01, 0.01)
            ask = bid + random.uniform(0.0001, 0.0005)
            price_widget.update_price(symbol, bid, ask)
        
        root.after(1000, update_prices)  # Update every second
    
    update_prices()
    
    root.mainloop()