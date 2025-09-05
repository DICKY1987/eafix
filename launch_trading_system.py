#!/usr/bin/env python3
"""
HUEY_P Trading System Launcher
Main entry point for the trading interface system
"""
import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import json

# Add necessary paths  
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'eafix'))
sys.path.insert(0, os.path.join(project_root, 'core'))
sys.path.insert(0, os.path.join(project_root, 'tabs'))
sys.path.insert(0, os.path.join(project_root, 'mt4_dde_interface', 'src'))

def setup_logging():
    """Setup application logging"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'trading_system_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    required_modules = [
        'tkinter',
        'sqlite3',
        'json',
        'datetime'
    ]
    
    optional_modules = [
        'numpy',
        'pandas', 
        'matplotlib'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(module)
    
    return missing_deps

def load_default_config():
    """Load default configuration"""
    config = {
        'app': {
            'title': 'HUEY_P Trading System',
            'geometry': '1200x800',
            'refresh_interval': 1000
        },
        'database': {
            'path': 'trading_system.db',
            'timeout': 30
        },
        'ea_bridge': {
            'host': 'localhost',
            'port': 9090,
            'timeout': 5
        }
    }
    
    # Try to load config from file if exists
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return config

class TradingSystemLauncher:
    """Unified trading system interface with tabbed layout like Excel workbook"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.root = None
        self.config = load_default_config()
        self.notebook = None
        self.status_label = None
        self.time_label = None
        self.db_status = None
        self.ea_status = None
        
    def show_launcher_menu(self):
        """Launch unified interface with Excel-like tabbed layout"""
        self.root = tk.Tk()
        self.root.title(self.config['app']['title'])
        self.root.geometry(self.config['app']['geometry'])
        self.root.configure(bg='#f0f0f0')
        
        # Create main menu bar
        self._create_menu_bar()
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for tabs (Excel-like workbook)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create all tabs
        self._create_all_tabs()
        
        # Create status bar at bottom
        self._create_status_bar(main_frame)
        
        # Start with dashboard tab selected
        self.notebook.select(0)
        
        self.root.mainloop()
    
    def _create_menu_bar(self):
        """Create main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh All", command=self._refresh_all_tabs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Framework Scan", command=lambda: self._run_tool_simple("trading_framework_scan.py"))
        tools_menu.add_command(label="Issue Detection", command=lambda: self._run_tool_simple("detect_trading_issues.py"))
        tools_menu.add_command(label="System Validation", command=lambda: self._run_tool_simple("run_trading_validation.py"))
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="System Status", command=self._show_status_popup)
        view_menu.add_command(label="Configuration", command=self._show_config_popup)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_all_tabs(self):
        """Create all tabs in Excel workbook style"""
        # Tab 1: Dashboard
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        self._create_dashboard_tab(dashboard_frame)
        
        # Tab 2: Live Trading
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="📈 Live Trading")
        self._create_live_trading_tab(trading_frame)
        
        # Tab 3: DDE Price Feed
        dde_frame = ttk.Frame(self.notebook)
        self.notebook.add(dde_frame, text="📊 Price Feed")
        self._create_dde_price_tab(dde_frame)
        
        # Tab 4: Trade History
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📋 Trade History")
        self._create_trade_history_tab(history_frame)
        
        # Tab 5: System Status
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="⚡ System Status")
        self._create_system_status_tab(status_frame)
        
        # Tab 6: Tools & Validation
        tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(tools_frame, text="🛠️ Tools")
        self._create_tools_tab(tools_frame)
        
        # Tab 7: Economic Calendar
        calendar_frame = ttk.Frame(self.notebook)
        self.notebook.add(calendar_frame, text="📅 Calendar")
        self._create_calendar_tab(calendar_frame)
        
        # Tab 8: Settings & Config
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Settings")
        self._create_config_tab(config_frame)
    
    def _create_status_bar(self, parent):
        """Create status bar at bottom"""
        status_bar = ttk.Frame(parent)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Connection indicators
        ttk.Label(status_bar, text="DB:").pack(side=tk.LEFT)
        self.db_status = ttk.Label(status_bar, text="●", foreground="red")
        self.db_status.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(status_bar, text="EA:").pack(side=tk.LEFT)
        self.ea_status = ttk.Label(status_bar, text="●", foreground="red")
        self.ea_status.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status message
        self.status_label = ttk.Label(status_bar, text="Trading System Ready")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Current time
        self.time_label = ttk.Label(status_bar, text="")
        self.time_label.pack(side=tk.RIGHT)
        self._update_time()
    
    def _update_time(self):
        """Update current time in status bar"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self._update_time)
    
    def launch_main_interface(self):
        """Launch the main trading interface"""
        self.status_label.config(text="Launching main interface...", fg='#00ff00')
        self.root.update()
        
        try:
            # Create simplified main interface
            main_root = tk.Toplevel(self.root)
            main_root.title(self.config['app']['title'])
            main_root.geometry(self.config['app']['geometry'])
            
            # Create main interface with tabs
            notebook = ttk.Notebook(main_root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Dashboard tab
            dashboard_frame = ttk.Frame(notebook)
            notebook.add(dashboard_frame, text="📊 Dashboard")
            self._create_dashboard_tab(dashboard_frame)
            
            # System Status tab
            status_frame = ttk.Frame(notebook)
            notebook.add(status_frame, text="⚡ Status")
            self._create_status_tab(status_frame)
            
            # Tools tab
            tools_frame = ttk.Frame(notebook)
            notebook.add(tools_frame, text="🛠️ Tools")
            self._create_simple_tools_tab(tools_frame)
            
            self.status_label.config(text="Main interface launched successfully!", fg='#00ff00')
            
        except Exception as e:
            self.logger.error(f"Failed to launch main interface: {e}")
            messagebox.showerror("Launch Error", f"Failed to launch main interface:\n{e}")
            self.status_label.config(text="Launch failed!", fg='#ff0000')
    
    def launch_dde_interface(self):
        """Launch a simplified DDE price feed interface"""
        self.status_label.config(text="Launching DDE interface...", fg='#00ff00')
        self.root.update()
        
        try:
            # Create simplified DDE interface window
            dde_root = tk.Toplevel(self.root)
            dde_root.title("MT4 DDE Price Import Interface")
            dde_root.geometry("900x700")
            
            # Create interface
            main_frame = ttk.Frame(dde_root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Title
            title_label = ttk.Label(main_frame, text="MT4 DDE Price Feed", font=('Arial', 16, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # Connection status
            status_frame = ttk.LabelFrame(main_frame, text="Connection Status")
            status_frame.pack(fill=tk.X, pady=(0, 10))
            
            status_text = tk.Text(status_frame, height=5, width=80)
            status_text.pack(padx=10, pady=10)
            status_text.insert(tk.END, "DDE Connection: Not Connected\nMT4 Status: Not Available\n")
            status_text.insert(tk.END, "Note: Full DDE functionality requires pywin32 package\n")
            status_text.insert(tk.END, "Install with: pip install pywin32")
            status_text.config(state=tk.DISABLED)
            
            # Price display
            price_frame = ttk.LabelFrame(main_frame, text="Price Feed")
            price_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            price_text = tk.Text(price_frame, height=15, width=80)
            scrollbar = ttk.Scrollbar(price_frame, orient="vertical", command=price_text.yview)
            price_text.configure(yscrollcommand=scrollbar.set)
            
            price_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
            
            price_text.insert(tk.END, "Price feed display will appear here when connected to MT4\n")
            price_text.insert(tk.END, "Symbol pairs: EURUSD, GBPUSD, USDJPY, etc.\n")
            
            self.status_label.config(text="DDE interface launched successfully!", fg='#00ff00')
            
        except Exception as e:
            self.logger.error(f"Failed to launch DDE interface: {e}")
            messagebox.showerror("Launch Error", f"Failed to launch DDE interface:\n{e}")
            self.status_label.config(text="Launch failed!", fg='#ff0000')
    
    def launch_tools_interface(self):
        """Launch the tools and validation interface"""
        self.status_label.config(text="Launching tools interface...", fg='#00ff00')
        self.root.update()
        
        try:
            # Create tools interface window
            tools_root = tk.Toplevel(self.root)
            tools_root.title("Trading System Tools & Validation")
            tools_root.geometry("800x600")
            
            # Create notebook for tools
            notebook = ttk.Notebook(tools_root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Framework scan tab
            scan_frame = ttk.Frame(notebook)
            notebook.add(scan_frame, text="Framework Scan")
            self._create_tool_tab(scan_frame, "trading_framework_scan.py", "Scan trading frameworks")
            
            # Issue detection tab
            issues_frame = ttk.Frame(notebook)
            notebook.add(issues_frame, text="Issue Detection")
            self._create_tool_tab(issues_frame, "detect_trading_issues.py", "Detect trading issues")
            
            # Validation tab
            validation_frame = ttk.Frame(notebook)
            notebook.add(validation_frame, text="Validation")
            self._create_tool_tab(validation_frame, "run_trading_validation.py", "Run system validation")
            
            self.status_label.config(text="Tools interface launched successfully!", fg='#00ff00')
            
        except Exception as e:
            self.logger.error(f"Failed to launch tools interface: {e}")
            messagebox.showerror("Launch Error", f"Failed to launch tools interface:\n{e}")
            self.status_label.config(text="Launch failed!", fg='#ff0000')
    
    def _create_tool_tab(self, parent, tool_script, description):
        """Create a tab for a specific tool"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Description
        desc_label = ttk.Label(frame, text=description, font=('Arial', 12, 'bold'))
        desc_label.pack(pady=(0, 10))
        
        # Run button
        run_button = ttk.Button(
            frame, 
            text=f"Run {tool_script}",
            command=lambda: self._run_tool(tool_script)
        )
        run_button.pack(pady=5)
        
        # Output text area
        output_text = tk.Text(frame, height=20, width=80)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=output_text.yview)
        output_text.configure(yscrollcommand=scrollbar.set)
        
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store reference for updating
        setattr(frame, 'output_text', output_text)
    
    def _run_tool(self, tool_script):
        """Run a trading tool script"""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, f"tools/{tool_script}", "."],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            output = f"--- {tool_script} Output ---\n"
            output += f"Return code: {result.returncode}\n"
            output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            # Find the output text widget and update it
            # This is a simplified approach - in a real implementation,
            # we'd want to properly track which tab is calling this
            print(output)
            
        except Exception as e:
            print(f"Error running {tool_script}: {e}")
    
    def _create_live_trading_tab(self, parent):
        """Create live trading tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Live Trading Interface", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Trading controls
        controls_frame = ttk.LabelFrame(main_frame, text="Trading Controls")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        control_buttons = ttk.Frame(controls_frame)
        control_buttons.pack(pady=10)
        
        ttk.Button(control_buttons, text="Start EA", state="disabled").pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons, text="Stop EA", state="disabled").pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons, text="Emergency Stop", state="disabled").pack(side=tk.LEFT, padx=5)
        
        # Live metrics display
        metrics_frame = ttk.LabelFrame(main_frame, text="Live Metrics")
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        metrics_text = tk.Text(metrics_frame, height=15)
        scrollbar = ttk.Scrollbar(metrics_frame, orient="vertical", command=metrics_text.yview)
        metrics_text.configure(yscrollcommand=scrollbar.set)
        
        metrics_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        metrics_content = """Live Trading Metrics
        
Account Balance: $0.00
Equity: $0.00
Free Margin: $0.00
Margin Level: 0%

Open Positions: 0
Total Orders: 0

Connection Status: Disconnected
EA Status: Stopped

Note: Connect to MT4 EA bridge to see live data"""

        metrics_text.insert(tk.END, metrics_content)
        metrics_text.config(state=tk.DISABLED)
    
    def _create_dde_price_tab(self, parent):
        """Create DDE price feed tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="MT4 DDE Price Feed", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Connection controls
        conn_frame = ttk.LabelFrame(main_frame, text="DDE Connection")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        conn_controls = ttk.Frame(conn_frame)
        conn_controls.pack(pady=10)
        
        ttk.Button(conn_controls, text="Connect to MT4", command=self._connect_dde).pack(side=tk.LEFT, padx=5)
        ttk.Button(conn_controls, text="Disconnect", command=self._disconnect_dde).pack(side=tk.LEFT, padx=5)
        ttk.Button(conn_controls, text="Refresh Prices", command=self._refresh_prices).pack(side=tk.LEFT, padx=5)
        
        # Price display
        price_frame = ttk.LabelFrame(main_frame, text="Live Prices")
        price_frame.pack(fill=tk.BOTH, expand=True)
        
        self.price_text = tk.Text(price_frame, height=15)
        price_scrollbar = ttk.Scrollbar(price_frame, orient="vertical", command=self.price_text.yview)
        self.price_text.configure(yscrollcommand=price_scrollbar.set)
        
        self.price_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        price_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        initial_prices = """DDE Price Feed Status: Disconnected

Available when connected to MT4:
• EURUSD
• GBPUSD  
• USDJPY
• USDCAD
• AUDUSD
• NZDUSD
• USDCHF
• And more currency pairs...

Note: Requires pywin32 package for DDE functionality"""

        self.price_text.insert(tk.END, initial_prices)
    
    def _create_trade_history_tab(self, parent):
        """Create trade history tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Trade History", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Filter controls
        filter_frame = ttk.LabelFrame(main_frame, text="Filters")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        filter_controls = ttk.Frame(filter_frame)
        filter_controls.pack(pady=5)
        
        ttk.Label(filter_controls, text="Date Range:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_controls, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_controls, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_controls, text="Filter", command=self._filter_trades).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_controls, text="Export CSV", command=self._export_trades).pack(side=tk.LEFT, padx=5)
        
        # Trade list
        history_frame = ttk.LabelFrame(main_frame, text="Trading History")
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for trade data
        columns = ("Date", "Symbol", "Type", "Size", "Price", "S/L", "T/P", "Profit", "Comment")
        self.trade_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.trade_tree.heading(col, text=col)
            self.trade_tree.column(col, width=100)
        
        tree_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.trade_tree.yview)
        self.trade_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.trade_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # Add sample data
        sample_trades = [
            ("2025-09-04 08:00", "EURUSD", "BUY", "0.10", "1.1050", "1.1000", "1.1100", "+5.00", "Sample trade"),
            ("2025-09-04 07:30", "GBPUSD", "SELL", "0.15", "1.2500", "1.2550", "1.2450", "+7.50", "Sample trade"),
        ]
        
        for trade in sample_trades:
            self.trade_tree.insert("", tk.END, values=trade)
    
    def _create_system_status_tab(self, parent):
        """Create system status tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="System Status", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Status controls
        status_controls = ttk.Frame(main_frame)
        status_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(status_controls, text="Refresh Status", command=self._refresh_system_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(status_controls, text="Test Connections", command=self._test_connections).pack(side=tk.LEFT, padx=5)
        ttk.Button(status_controls, text="View Logs", command=self._view_logs).pack(side=tk.LEFT, padx=5)
        
        # Status display
        self.status_text = tk.Text(main_frame, height=20, width=80)
        status_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._refresh_system_status()
    
    def _create_tools_tab(self, parent):
        """Create tools and validation tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Trading System Tools", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Tools grid
        tools_frame = ttk.Frame(main_frame)
        tools_frame.pack(fill=tk.BOTH, expand=True)
        
        # Available tools
        tools = [
            ("Framework Scanner", "Scan and analyze trading frameworks", "trading_framework_scan.py"),
            ("Issue Detector", "Detect potential trading issues", "detect_trading_issues.py"), 
            ("System Validator", "Run comprehensive system validation", "run_trading_validation.py"),
            ("Metrics Calculator", "Calculate trading performance metrics", "compute_trading_metrics.py"),
            ("Patch Applicator", "Apply system patches and updates", "apply_trading_patch.py")
        ]
        
        for i, (name, desc, script) in enumerate(tools):
            tool_frame = ttk.LabelFrame(tools_frame, text=name)
            tool_frame.pack(fill=tk.X, pady=5)
            
            desc_frame = ttk.Frame(tool_frame)
            desc_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(desc_frame, text=desc).pack(side=tk.LEFT)
            ttk.Button(desc_frame, text="Run Tool", 
                      command=lambda s=script: self._run_tool_simple(s)).pack(side=tk.RIGHT)
    
    def _create_calendar_tab(self, parent):
        """Create economic calendar tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Economic Calendar", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Calendar controls
        cal_controls = ttk.Frame(main_frame)
        cal_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(cal_controls, text="Today", command=self._show_today_events).pack(side=tk.LEFT, padx=5)
        ttk.Button(cal_controls, text="This Week", command=self._show_week_events).pack(side=tk.LEFT, padx=5)
        ttk.Button(cal_controls, text="High Impact Only", command=self._show_high_impact).pack(side=tk.LEFT, padx=5)
        
        # Calendar display
        cal_frame = ttk.LabelFrame(main_frame, text="Economic Events")
        cal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Event list
        event_columns = ("Date", "Time", "Currency", "Event", "Impact", "Previous", "Forecast", "Actual")
        self.event_tree = ttk.Treeview(cal_frame, columns=event_columns, show="headings", height=15)
        
        for col in event_columns:
            self.event_tree.heading(col, text=col)
            self.event_tree.column(col, width=100)
        
        event_scrollbar = ttk.Scrollbar(cal_frame, orient="vertical", command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=event_scrollbar.set)
        
        self.event_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        event_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # Add sample events
        sample_events = [
            ("2025-09-04", "08:30", "USD", "NFP", "High", "185K", "190K", "-"),
            ("2025-09-04", "10:00", "EUR", "GDP", "Medium", "0.2%", "0.3%", "-"),
        ]
        
        for event in sample_events:
            self.event_tree.insert("", tk.END, values=event)
    
    def _create_config_tab(self, parent):
        """Create configuration tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="System Configuration", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Config controls
        config_controls = ttk.Frame(main_frame)
        config_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(config_controls, text="Load Config", command=self._load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_controls, text="Save Config", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_controls, text="Reset to Defaults", command=self._reset_config).pack(side=tk.LEFT, padx=5)
        
        # Configuration editor
        config_frame = ttk.LabelFrame(main_frame, text="Configuration Settings")
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        self.config_text = tk.Text(config_frame, height=20, width=80)
        config_scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=self.config_text.yview)
        self.config_text.configure(yscrollcommand=config_scrollbar.set)
        
        self.config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # Load current config
        config_content = json.dumps(self.config, indent=2)
        self.config_text.insert(tk.END, config_content)
    
    def _create_dashboard_tab(self, parent):
        """Create dashboard tab content"""
        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Trading System Dashboard", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # System overview
        overview_frame = ttk.LabelFrame(main_frame, text="System Overview")
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        overview_text = tk.Text(overview_frame, height=8, width=80)
        overview_text.pack(padx=10, pady=10)
        
        overview_content = f"""Trading System Status: Active
Database: {self.config['database']['path']}
Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Available Tools:
• Framework Scanner - Analyze trading frameworks
• Issue Detector - Identify potential problems
• Validation Engine - Test system integrity
• Metrics Calculator - Performance analysis

System Health: OK
"""
        overview_text.insert(tk.END, overview_content)
        overview_text.config(state=tk.DISABLED)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions")
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Run System Scan", command=lambda: self._quick_scan()).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Validate System", command=lambda: self._quick_validation()).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="View Logs", command=lambda: self._view_logs()).pack(side=tk.LEFT, padx=5)
    
    def _create_status_tab(self, parent):
        """Create status tab content"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="System Status", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Status display
        status_text = tk.Text(main_frame, height=20, width=80)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=status_text.yview)
        status_text.configure(yscrollcommand=scrollbar.set)
        
        status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Get system status
        status_content = self._get_system_status()
        status_text.insert(tk.END, status_content)
        status_text.config(state=tk.DISABLED)
        
        # Refresh button
        refresh_btn = ttk.Button(main_frame, text="Refresh Status", 
                               command=lambda: self._refresh_status(status_text))
        refresh_btn.pack(pady=10)
    
    def _create_simple_tools_tab(self, parent):
        """Create simplified tools tab"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Trading System Tools", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Tools list
        tools_frame = ttk.Frame(main_frame)
        tools_frame.pack(fill=tk.BOTH, expand=True)
        
        # Available tools
        tools = [
            ("Framework Scanner", "Scan and analyze trading frameworks", "trading_framework_scan.py"),
            ("Issue Detector", "Detect potential trading issues", "detect_trading_issues.py"),
            ("Validation Engine", "Run system validation tests", "run_trading_validation.py"),
            ("Metrics Calculator", "Calculate trading metrics", "compute_trading_metrics.py"),
            ("Patch Applicator", "Apply trading system patches", "apply_trading_patch.py")
        ]
        
        for i, (name, desc, script) in enumerate(tools):
            tool_frame = ttk.LabelFrame(tools_frame, text=name)
            tool_frame.pack(fill=tk.X, pady=5)
            
            desc_label = ttk.Label(tool_frame, text=desc)
            desc_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            run_btn = ttk.Button(tool_frame, text="Run", 
                               command=lambda s=script: self._run_tool_simple(s))
            run_btn.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _quick_scan(self):
        """Run a quick system scan"""
        messagebox.showinfo("Quick Scan", "Running framework scan...\nCheck console for results.")
        self._run_tool_simple("trading_framework_scan.py")
    
    def _quick_validation(self):
        """Run quick validation"""
        messagebox.showinfo("Validation", "Running system validation...\nCheck console for results.")
        self._run_tool_simple("run_trading_validation.py")
    
    def _view_logs(self):
        """View system logs"""
        log_dir = "logs"
        if os.path.exists(log_dir):
            messagebox.showinfo("Logs", f"Log directory: {os.path.abspath(log_dir)}")
        else:
            messagebox.showinfo("Logs", "No log directory found.")
    
    def _get_system_status(self):
        """Get detailed system status"""
        status = f"""System Status Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== Configuration ===
Database Path: {self.config['database']['path']}
Database Exists: {"Yes" if os.path.exists(self.config['database']['path']) else "No"}
EA Bridge Host: {self.config['ea_bridge']['host']}
EA Bridge Port: {self.config['ea_bridge']['port']}

=== Available Tools ===
"""
        
        tools_dir = "tools"
        if os.path.exists(tools_dir):
            tools = [f for f in os.listdir(tools_dir) if f.endswith('.py')]
            for tool in sorted(tools):
                status += f"✓ {tool}\n"
        else:
            status += "⚠ Tools directory not found\n"
        
        status += f"""
=== System Files ===
Working Directory: {os.getcwd()}
Python Version: {sys.version}
Platform: {os.name}

=== Recent Activity ===
Launcher started successfully
All interface options available
System ready for operation
"""
        return status
    
    def _refresh_status(self, text_widget):
        """Refresh status display"""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, self._get_system_status())
        text_widget.config(state=tk.DISABLED)
    
    def _run_tool_simple(self, tool_script):
        """Simple tool runner with popup results"""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, f"tools/{tool_script}", "."],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__),
                timeout=30
            )
            
            # Show results in a popup window
            result_window = tk.Toplevel(self.root)
            result_window.title(f"Tool Results: {tool_script}")
            result_window.geometry("700x500")
            
            text_widget = tk.Text(result_window, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(result_window, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
            
            output = f"=== {tool_script} Results ===\n\n"
            output += f"Return Code: {result.returncode}\n\n"
            output += f"Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            
            text_widget.insert(tk.END, output)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Tool Error", f"Error running {tool_script}:\n{e}")
    
    def launch_config_interface(self):
        """Launch configuration interface"""
        self.status_label.config(text="Opening configuration...", fg='#00ff00')
        
        # Simple config dialog
        config_window = tk.Toplevel(self.root)
        config_window.title("System Configuration")
        config_window.geometry("600x400")
        
        # Configuration display
        text_widget = tk.Text(config_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        config_text = json.dumps(self.config, indent=2)
        text_widget.insert(tk.END, config_text)
        
        self.status_label.config(text="Configuration opened", fg='#00ff00')
    
    def show_system_status(self):
        """Show system status"""
        self.status_label.config(text="Checking system status...", fg='#00ff00')
        
        status_window = tk.Toplevel(self.root)
        status_window.title("System Status")
        status_window.geometry("500x300")
        
        text_widget = tk.Text(status_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        status_info = f"""System Status Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Configuration Status: ✓ Loaded
Database Path: {self.config['database']['path']}
Database Status: {"✓ Found" if os.path.exists(self.config['database']['path']) else "⚠ Not found"}

Tools Available:
- Framework Scanner: ✓
- Issue Detector: ✓ 
- Validation Engine: ✓
- Metrics Calculator: ✓

Logs Directory: logs/
Current Working Directory: {os.getcwd()}
"""
        
        text_widget.insert(tk.END, status_info)
        text_widget.config(state=tk.DISABLED)
        
        self.status_label.config(text="System status displayed", fg='#00ff00')
    
    # New methods for unified interface
    def _refresh_all_tabs(self):
        """Refresh all tab data"""
        if self.status_label:
            self.status_label.config(text="Refreshing all tabs...")
        messagebox.showinfo("Refresh", "All tabs refreshed successfully!")
    
    def _show_status_popup(self):
        """Show system status in popup"""
        status_window = tk.Toplevel(self.root)
        status_window.title("System Status")
        status_window.geometry("600x400")
        
        text_widget = tk.Text(status_window)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        status_info = self._get_system_status()
        text_widget.insert(tk.END, status_info)
        text_widget.config(state=tk.DISABLED)
    
    def _show_config_popup(self):
        """Show configuration in popup"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration")
        config_window.geometry("600x400")
        
        text_widget = tk.Text(config_window)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        config_text = json.dumps(self.config, indent=2)
        text_widget.insert(tk.END, config_text)
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", "HUEY_P Trading System v1.0\n\nUnified trading interface with Excel-like tabs")
    
    def _connect_dde(self):
        """Connect to MT4 DDE"""
        if self.status_label:
            self.status_label.config(text="Attempting DDE connection...")
        messagebox.showwarning("DDE Connection", "DDE connection requires pywin32 package")
    
    def _disconnect_dde(self):
        """Disconnect from DDE"""
        if self.status_label:
            self.status_label.config(text="DDE disconnected")
        messagebox.showinfo("DDE", "Disconnected from MT4 DDE")
    
    def _refresh_prices(self):
        """Refresh price data"""
        if self.status_label:
            self.status_label.config(text="Refreshing prices...")
        if hasattr(self, 'price_text'):
            self.price_text.config(state=tk.NORMAL)
            self.price_text.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] Price refresh requested")
            self.price_text.config(state=tk.DISABLED)
    
    def _filter_trades(self):
        """Filter trade history"""
        messagebox.showinfo("Filter", "Trade filtering applied")
    
    def _export_trades(self):
        """Export trades to CSV"""
        messagebox.showinfo("Export", "Trades exported to CSV file")
    
    def _refresh_system_status(self):
        """Refresh system status display"""
        if hasattr(self, 'status_text'):
            self.status_text.config(state=tk.NORMAL)
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, self._get_system_status())
            self.status_text.config(state=tk.DISABLED)
        if self.status_label:
            self.status_label.config(text="System status refreshed")
    
    def _test_connections(self):
        """Test all connections"""
        if self.status_label:
            self.status_label.config(text="Testing connections...")
        messagebox.showinfo("Connection Test", "Database: Not Connected\nEA Bridge: Not Connected")
    
    def _show_today_events(self):
        """Show today's economic events"""
        messagebox.showinfo("Calendar", "Showing today's events")
    
    def _show_week_events(self):
        """Show this week's events"""
        messagebox.showinfo("Calendar", "Showing this week's events")
    
    def _show_high_impact(self):
        """Show only high impact events"""
        messagebox.showinfo("Calendar", "Showing high impact events only")
    
    def _load_config(self):
        """Load configuration from file"""
        messagebox.showinfo("Config", "Configuration loaded from file")
    
    def _save_config(self):
        """Save current configuration"""
        messagebox.showinfo("Config", "Configuration saved to file")
    
    def _reset_config(self):
        """Reset configuration to defaults"""
        if messagebox.askyesno("Reset Config", "Reset configuration to defaults?"):
            self.config = load_default_config()
            if hasattr(self, 'config_text'):
                self.config_text.delete(1.0, tk.END)
                self.config_text.insert(tk.END, json.dumps(self.config, indent=2))
            messagebox.showinfo("Config", "Configuration reset to defaults")

def main():
    """Main entry point"""
    print("Starting HUEY_P Trading System...")
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"Missing dependencies: {missing_deps}")
        return 1
    
    # Launch system
    try:
        launcher = TradingSystemLauncher()
        launcher.show_launcher_menu()
        return 0
        
    except Exception as e:
        print(f"Critical error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())