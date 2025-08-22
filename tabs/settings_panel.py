"""
HUEY_P Trading Interface - Settings Panel Tab
Configuration management and preferences
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SettingsPanel:
    """Settings and configuration management panel"""
    
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app_controller = app_controller
        self.frame = None
        
        # Settings categories
        self.current_settings = {}
        self.original_settings = {}
        self.has_changes = False
        
        # Configuration file paths
        self.config_files = {
            'interface': 'HUEY_PPYTH_config.yaml',
            'claude_trading': 'Config/claude_trading_config.yaml',
            'broker_settings': 'Config/broker_settings.yaml'
        }
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the settings panel UI"""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Create layout
        self.create_layout()
        
        # Setup components
        self.setup_settings_tree()
        self.setup_settings_editor()
        self.setup_control_buttons()
        
        logger.info("Settings panel UI setup complete")
    
    def create_layout(self):
        """Create the main layout structure"""
        # Main container with padding
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row - Info and controls
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(top_frame, 
                              text="⚙️ Configure system settings and preferences. Changes require restart to take effect.",
                              font=('Arial', 10))
        info_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.changes_label = ttk.Label(top_frame, text="No changes", foreground="gray")
        self.changes_label.pack(side=tk.RIGHT)
        
        # Main content - split into tree and editor
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left panel - Settings tree
        self.tree_frame = ttk.LabelFrame(content_frame, text="📁 Settings Categories", padding=10)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Right panel - Settings editor
        self.editor_frame = ttk.LabelFrame(content_frame, text="✏️ Edit Settings", padding=10)
        self.editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Bottom row - Control buttons
        self.controls_frame = ttk.Frame(main_container)
        self.controls_frame.pack(fill=tk.X)
    
    def setup_settings_tree(self):
        """Setup settings categories tree"""
        # Settings tree
        self.settings_tree = ttk.Treeview(self.tree_frame, show='tree')
        self.settings_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure column width
        self.settings_tree.column('#0', width=200)
        
        # Populate tree with settings categories
        self.populate_settings_tree()
        
        # Bind selection event
        self.settings_tree.bind('<<TreeviewSelect>>', self.on_category_selected)
    
    def setup_settings_editor(self):
        """Setup settings editor panel"""
        # Create notebook for different setting types
        self.editor_notebook = ttk.Notebook(self.editor_frame)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Interface settings tab
        self.setup_interface_settings()
        
        # Trading settings tab
        self.setup_trading_settings()
        
        # Broker settings tab
        self.setup_broker_settings()
        
        # Advanced settings tab
        self.setup_advanced_settings()
    
    def setup_interface_settings(self):
        """Setup interface settings tab"""
        interface_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(interface_frame, text="Interface")
        
        # Create scrollable frame
        canvas = tk.Canvas(interface_frame)
        scrollbar = ttk.Scrollbar(interface_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Application settings
        app_frame = ttk.LabelFrame(scrollable_frame, text="Application", padding=10)
        app_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Window settings
        ttk.Label(app_frame, text="Window Width:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.window_width_var = tk.StringVar()
        ttk.Entry(app_frame, textvariable=self.window_width_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(app_frame, text="Window Height:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.window_height_var = tk.StringVar()
        ttk.Entry(app_frame, textvariable=self.window_height_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(app_frame, text="Refresh Interval (ms):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.refresh_interval_var = tk.StringVar()
        ttk.Entry(app_frame, textvariable=self.refresh_interval_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Display settings
        display_frame = ttk.LabelFrame(scrollable_frame, text="Display", padding=10)
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(display_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(display_frame, textvariable=self.theme_var,
                                  values=["default", "clam", "alt", "classic"], state="readonly")
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(display_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.font_size_var = tk.StringVar()
        ttk.Entry(display_frame, textvariable=self.font_size_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        self.show_tooltips_var = tk.BooleanVar()
        ttk.Checkbutton(display_frame, text="Show Tooltips", variable=self.show_tooltips_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_trading_settings(self):
        """Setup trading settings tab"""
        trading_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(trading_frame, text="Trading")
        
        # Create scrollable frame
        canvas = tk.Canvas(trading_frame)
        scrollbar = ttk.Scrollbar(trading_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Risk Management
        risk_frame = ttk.LabelFrame(scrollable_frame, text="Risk Management", padding=10)
        risk_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(risk_frame, text="Risk Percent per Trade:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.risk_percent_var = tk.StringVar()
        ttk.Entry(risk_frame, textvariable=self.risk_percent_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(risk_frame, text="%").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(risk_frame, text="Max Daily Drawdown:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_drawdown_var = tk.StringVar()
        ttk.Entry(risk_frame, textvariable=self.max_drawdown_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(risk_frame, text="%").grid(row=1, column=2, sticky=tk.W)
        
        ttk.Label(risk_frame, text="Max Concurrent Trades:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_trades_var = tk.StringVar()
        ttk.Entry(risk_frame, textvariable=self.max_trades_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Trading Parameters
        params_frame = ttk.LabelFrame(scrollable_frame, text="Trading Parameters", padding=10)
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.simulation_mode_var = tk.BooleanVar()
        ttk.Checkbutton(params_frame, text="Simulation Mode", variable=self.simulation_mode_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.auto_trading_var = tk.BooleanVar()
        ttk.Checkbutton(params_frame, text="Auto Trading Enabled", variable=self.auto_trading_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Label(params_frame, text="Magic Number:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.magic_number_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.magic_number_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_broker_settings(self):
        """Setup broker settings tab"""
        broker_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(broker_frame, text="Broker")
        
        # Create scrollable frame
        canvas = tk.Canvas(broker_frame)
        scrollbar = ttk.Scrollbar(broker_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Connection settings
        conn_frame = ttk.LabelFrame(scrollable_frame, text="Connection", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(conn_frame, text="Server Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.server_name_var = tk.StringVar()
        ttk.Entry(conn_frame, textvariable=self.server_name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(conn_frame, text="Account Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.account_type_var = tk.StringVar()
        account_combo = ttk.Combobox(conn_frame, textvariable=self.account_type_var,
                                   values=["demo", "live"], state="readonly")
        account_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(conn_frame, text="EA Bridge Port:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.bridge_port_var = tk.StringVar()
        ttk.Entry(conn_frame, textvariable=self.bridge_port_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Timezone settings
        tz_frame = ttk.LabelFrame(scrollable_frame, text="Timezone", padding=10)
        tz_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tz_frame, text="Server Timezone Offset:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.server_tz_var = tk.StringVar()
        ttk.Entry(tz_frame, textvariable=self.server_tz_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(tz_frame, text="hours").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(tz_frame, text="User Timezone Offset:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.user_tz_var = tk.StringVar()
        ttk.Entry(tz_frame, textvariable=self.user_tz_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(tz_frame, text="hours").grid(row=1, column=2, sticky=tk.W)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_advanced_settings(self):
        """Setup advanced settings tab"""
        advanced_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(advanced_frame, text="Advanced")
        
        # Create scrollable frame
        canvas = tk.Canvas(advanced_frame)
        scrollbar = ttk.Scrollbar(advanced_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Database settings
        db_frame = ttk.LabelFrame(scrollable_frame, text="Database", padding=10)
        db_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(db_frame, text="Database Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.db_path_var = tk.StringVar()
        ttk.Entry(db_frame, textvariable=self.db_path_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=(10, 5))
        ttk.Button(db_frame, text="Browse", command=self.browse_database).grid(row=0, column=2, padx=(5, 0))
        
        self.backup_on_start_var = tk.BooleanVar()
        ttk.Checkbutton(db_frame, text="Backup on Start", variable=self.backup_on_start_var).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # Logging settings
        log_frame = ttk.LabelFrame(scrollable_frame, text="Logging", padding=10)
        log_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(log_frame, text="Log Level:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.log_level_var = tk.StringVar()
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var,
                               values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly")
        log_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        self.log_to_file_var = tk.BooleanVar()
        ttk.Checkbutton(log_frame, text="Log to File", variable=self.log_to_file_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Performance settings
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(perf_frame, text="Cache Duration (seconds):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cache_duration_var = tk.StringVar()
        ttk.Entry(perf_frame, textvariable=self.cache_duration_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(perf_frame, text="Connection Timeout (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.connection_timeout_var = tk.StringVar()
        ttk.Entry(perf_frame, textvariable=self.connection_timeout_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_control_buttons(self):
        """Setup control buttons"""
        # Left side - Action buttons
        action_frame = ttk.Frame(self.controls_frame)
        action_frame.pack(side=tk.LEFT)
        
        ttk.Button(action_frame, text="💾 Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="🔄 Reset to Default", command=self.reset_to_default).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="📤 Export Config", command=self.export_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="📥 Import Config", command=self.import_config).pack(side=tk.LEFT)
        
        # Right side - Status and help
        status_frame = ttk.Frame(self.controls_frame)
        status_frame.pack(side=tk.RIGHT)
        
        ttk.Button(status_frame, text="❓ Help", command=self.show_help).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(status_frame, text="🔄 Refresh", command=self.refresh_settings).pack(side=tk.RIGHT, padx=(10, 0))
    
    def populate_settings_tree(self):
        """Populate the settings tree with categories"""
        # Interface settings
        interface_node = self.settings_tree.insert('', 'end', text='Interface Settings', open=True)
        self.settings_tree.insert(interface_node, 'end', text='Application')
        self.settings_tree.insert(interface_node, 'end', text='Display')
        self.settings_tree.insert(interface_node, 'end', text='Notifications')
        
        # Trading settings
        trading_node = self.settings_tree.insert('', 'end', text='Trading Settings', open=True)
        self.settings_tree.insert(trading_node, 'end', text='Risk Management')
        self.settings_tree.insert(trading_node, 'end', text='Trading Parameters')
        self.settings_tree.insert(trading_node, 'end', text='Symbol Configuration')
        
        # Broker settings
        broker_node = self.settings_tree.insert('', 'end', text='Broker Settings', open=True)
        self.settings_tree.insert(broker_node, 'end', text='Connection')
        self.settings_tree.insert(broker_node, 'end', text='Account Settings')
        self.settings_tree.insert(broker_node, 'end', text='Timezone')
        
        # Advanced settings
        advanced_node = self.settings_tree.insert('', 'end', text='Advanced Settings', open=False)
        self.settings_tree.insert(advanced_node, 'end', text='Database')
        self.settings_tree.insert(advanced_node, 'end', text='Logging')
        self.settings_tree.insert(advanced_node, 'end', text='Performance')
        self.settings_tree.insert(advanced_node, 'end', text='Debug Options')
    
    def load_current_settings(self):
        """Load current settings from configuration files"""
        try:
            # Load interface settings
            config = self.app_controller.get_config()
            
            # Application settings
            app_config = config.get('app', {})
            self.window_width_var.set(str(app_config.get('width', 1400)))
            self.window_height_var.set(str(app_config.get('height', 900)))
            self.refresh_interval_var.set(str(app_config.get('refresh_interval', 1000)))
            
            # Display settings
            display_config = config.get('display', {})
            self.theme_var.set(display_config.get('theme', 'default'))
            self.font_size_var.set(str(display_config.get('font_size', 10)))
            self.show_tooltips_var.set(display_config.get('show_tooltips', True))
            
            # Database settings
            db_config = config.get('database', {})
            self.db_path_var.set(db_config.get('path', 'Database/trading_system.db'))
            self.backup_on_start_var.set(db_config.get('backup_on_start', True))
            
            # EA Bridge settings
            bridge_config = config.get('ea_bridge', {})
            self.bridge_port_var.set(str(bridge_config.get('port', 9999)))
            self.connection_timeout_var.set(str(bridge_config.get('timeout', 5)))
            
            # Load trading settings from external config files
            self.load_trading_config()
            self.load_broker_config()
            
            # Store original settings for change detection
            self.original_settings = self.get_current_form_values()
            self.has_changes = False
            
        except Exception as e:
            logger.error(f"Error loading current settings: {e}")
    
    def load_trading_config(self):
        """Load trading configuration from external file"""
        try:
            config_path = Path(self.config_files['claude_trading'])
            if config_path.exists():
                with open(config_path, 'r') as f:
                    trading_config = yaml.safe_load(f)
                
                self.risk_percent_var.set(str(trading_config.get('risk_percent_per_trade', 2.0)))
                self.max_drawdown_var.set(str(trading_config.get('max_daily_drawdown', 5.0)))
                self.max_trades_var.set(str(trading_config.get('max_concurrent_trades', 3)))
                self.simulation_mode_var.set(trading_config.get('simulation_mode', True))
                self.auto_trading_var.set(trading_config.get('auto_trading_enabled', False))
                self.magic_number_var.set(str(trading_config.get('magic_number', 12345)))
                
        except Exception as e:
            logger.error(f"Error loading trading config: {e}")
    
    def load_broker_config(self):
        """Load broker configuration from external file"""
        try:
            config_path = Path(self.config_files['broker_settings'])
            if config_path.exists():
                with open(config_path, 'r') as f:
                    broker_config = yaml.safe_load(f)
                
                self.server_name_var.set(broker_config.get('server_name', ''))
                self.account_type_var.set(broker_config.get('account_type', 'demo'))
                self.server_tz_var.set(str(broker_config.get('server_timezone_offset', 0)))
                self.user_tz_var.set(str(broker_config.get('user_timezone_offset', 0)))
                
        except Exception as e:
            logger.error(f"Error loading broker config: {e}")
    
    def get_current_form_values(self) -> Dict[str, Any]:
        """Get current values from all form fields"""
        return {
            'window_width': self.window_width_var.get(),
            'window_height': self.window_height_var.get(),
            'refresh_interval': self.refresh_interval_var.get(),
            'theme': self.theme_var.get(),
            'font_size': self.font_size_var.get(),
            'show_tooltips': self.show_tooltips_var.get(),
            'db_path': self.db_path_var.get(),
            'backup_on_start': self.backup_on_start_var.get(),
            'bridge_port': self.bridge_port_var.get(),
            'connection_timeout': self.connection_timeout_var.get(),
            'risk_percent': self.risk_percent_var.get(),
            'max_drawdown': self.max_drawdown_var.get(),
            'max_trades': self.max_trades_var.get(),
            'simulation_mode': self.simulation_mode_var.get(),
            'auto_trading': self.auto_trading_var.get(),
            'magic_number': self.magic_number_var.get(),
            'server_name': self.server_name_var.get(),
            'account_type': self.account_type_var.get(),
            'server_tz': self.server_tz_var.get(),
            'user_tz': self.user_tz_var.get()
        }
    
    def on_category_selected(self, event):
        """Handle settings category selection"""
        selection = self.settings_tree.selection()
        if selection:
            item = selection[0]
            category = self.settings_tree.item(item, 'text')
            logger.debug(f"Selected settings category: {category}")
            
            # Switch to appropriate tab based on category
            if 'Interface' in category or category in ['Application', 'Display', 'Notifications']:
                self.editor_notebook.select(0)  # Interface tab
            elif 'Trading' in category or category in ['Risk Management', 'Trading Parameters', 'Symbol Configuration']:
                self.editor_notebook.select(1)  # Trading tab
            elif 'Broker' in category or category in ['Connection', 'Account Settings', 'Timezone']:
                self.editor_notebook.select(2)  # Broker tab
            elif 'Advanced' in category or category in ['Database', 'Logging', 'Performance', 'Debug Options']:
                self.editor_notebook.select(3)  # Advanced tab
    
    def check_for_changes(self):
        """Check if settings have been modified"""
        current_values = self.get_current_form_values()
        has_changes = current_values != self.original_settings
        
        if has_changes != self.has_changes:
            self.has_changes = has_changes
            if has_changes:
                self.changes_label.config(text="● Unsaved changes", foreground="orange")
            else:
                self.changes_label.config(text="No changes", foreground="gray")
    
    def save_settings(self):
        """Save current settings to configuration files"""
        try:
            # Validate settings first
            if not self.validate_settings():
                return
            
            # Save interface settings
            self.save_interface_config()
            
            # Save trading settings
            self.save_trading_config()
            
            # Save broker settings
            self.save_broker_config()
            
            # Update original settings
            self.original_settings = self.get_current_form_values()
            self.has_changes = False
            self.changes_label.config(text="✓ Settings saved", foreground="green")
            
            # Show success message
            messagebox.showinfo("Settings Saved", 
                              "Settings have been saved successfully.\n\n" +
                              "Some changes may require restarting the application to take effect.")
            
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Save Error", f"Failed to save settings:\n{str(e)}")
    
    def validate_settings(self) -> bool:
        """Validate current settings"""
        try:
            # Validate numeric fields
            int(self.window_width_var.get())
            int(self.window_height_var.get())
            int(self.refresh_interval_var.get())
            int(self.font_size_var.get())
            int(self.bridge_port_var.get())
            int(self.connection_timeout_var.get())
            
            float(self.risk_percent_var.get())
            float(self.max_drawdown_var.get())
            int(self.max_trades_var.get())
            int(self.magic_number_var.get())
            
            float(self.server_tz_var.get())
            float(self.user_tz_var.get())
            
            # Validate ranges
            risk_percent = float(self.risk_percent_var.get())
            if not (0.1 <= risk_percent <= 10.0):
                raise ValueError("Risk percent must be between 0.1% and 10.0%")
            
            max_drawdown = float(self.max_drawdown_var.get())
            if not (1.0 <= max_drawdown <= 50.0):
                raise ValueError("Max drawdown must be between 1.0% and 50.0%")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid setting value:\n{str(e)}")
            return False
    
    def save_interface_config(self):
        """Save interface configuration"""
        config = {
            'app': {
                'title': 'HUEY_P Trading Interface',
                'width': int(self.window_width_var.get()),
                'height': int(self.window_height_var.get()),
                'refresh_interval': int(self.refresh_interval_var.get())
            },
            'database': {
                'path': self.db_path_var.get(),
                'backup_on_start': self.backup_on_start_var.get()
            },
            'ea_bridge': {
                'host': 'localhost',
                'port': int(self.bridge_port_var.get()),
                'timeout': int(self.connection_timeout_var.get()),
                'retry_interval': 10
            },
            'display': {
                'theme': self.theme_var.get(),
                'font_size': int(self.font_size_var.get()),
                'show_tooltips': self.show_tooltips_var.get()
            }
        }
        
        with open(self.config_files['interface'], 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def save_trading_config(self):
        """Save trading configuration"""
        config = {
            'risk_percent_per_trade': float(self.risk_percent_var.get()),
            'max_daily_drawdown': float(self.max_drawdown_var.get()),
            'max_concurrent_trades': int(self.max_trades_var.get()),
            'simulation_mode': self.simulation_mode_var.get(),
            'auto_trading_enabled': self.auto_trading_var.get(),
            'magic_number': int(self.magic_number_var.get())
        }
        
        config_path = Path(self.config_files['claude_trading'])
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def save_broker_config(self):
        """Save broker configuration"""
        config = {
            'server_name': self.server_name_var.get(),
            'account_type': self.account_type_var.get(),
            'server_timezone_offset': float(self.server_tz_var.get()),
            'user_timezone_offset': float(self.user_tz_var.get())
        }
        
        config_path = Path(self.config_files['broker_settings'])
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def reset_to_default(self):
        """Reset all settings to default values"""
        result = messagebox.askyesno("Reset to Default", 
                                   "This will reset all settings to their default values.\n\n" +
                                   "Are you sure you want to continue?")
        
        if result:
            # Reset to default values
            self.window_width_var.set("1400")
            self.window_height_var.set("900")
            self.refresh_interval_var.set("1000")
            self.theme_var.set("default")
            self.font_size_var.set("10")
            self.show_tooltips_var.set(True)
            
            self.db_path_var.set("Database/trading_system.db")
            self.backup_on_start_var.set(True)
            self.bridge_port_var.set("9999")
            self.connection_timeout_var.set("5")
            
            self.risk_percent_var.set("2.0")
            self.max_drawdown_var.set("5.0")
            self.max_trades_var.set("3")
            self.simulation_mode_var.set(True)
            self.auto_trading_var.set(False)
            self.magic_number_var.set("12345")
            
            self.server_name_var.set("")
            self.account_type_var.set("demo")
            self.server_tz_var.set("0")
            self.user_tz_var.set("0")
            
            self.check_for_changes()
            logger.info("Settings reset to default values")
    
    def export_config(self):
        """Export configuration to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".yaml",
                filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
                title="Export Configuration"
            )
            
            if filename:
                config = {
                    'exported_at': datetime.now().isoformat(),
                    'interface': self.get_current_form_values()
                }
                
                with open(filename, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                
                messagebox.showinfo("Export Successful", f"Configuration exported to:\n{filename}")
                logger.info(f"Configuration exported to: {filename}")
                
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            messagebox.showerror("Export Error", f"Failed to export configuration:\n{str(e)}")
    
    def import_config(self):
        """Import configuration from file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
                title="Import Configuration"
            )
            
            if filename:
                with open(filename, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Apply imported settings
                interface_config = config.get('interface', {})
                
                # Set values from imported config
                for key, value in interface_config.items():
                    if hasattr(self, f"{key}_var"):
                        var = getattr(self, f"{key}_var")
                        var.set(value)
                
                self.check_for_changes()
                messagebox.showinfo("Import Successful", f"Configuration imported from:\n{filename}")
                logger.info(f"Configuration imported from: {filename}")
                
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            messagebox.showerror("Import Error", f"Failed to import configuration:\n{str(e)}")
    
    def browse_database(self):
        """Browse for database file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db"), ("SQLite files", "*.sqlite"), ("All files", "*.*")],
            title="Select Database File"
        )
        
        if filename:
            self.db_path_var.set(filename)
            self.check_for_changes()
    
    def refresh_settings(self):
        """Refresh settings from configuration files"""
        if self.has_changes:
            result = messagebox.askyesno("Unsaved Changes", 
                                       "You have unsaved changes. Refreshing will discard them.\n\n" +
                                       "Are you sure you want to continue?")
            if not result:
                return
        
        self.load_current_settings()
        logger.info("Settings refreshed from configuration files")
    
    def show_help(self):
        """Show settings help dialog"""
        help_text = """
HUEY_P Trading Interface Settings Help

Interface Settings:
• Window Width/Height: Application window dimensions
• Refresh Interval: How often to update data (milliseconds)
• Theme: Visual appearance theme
• Font Size: Text size throughout application

Trading Settings:
• Risk Percent: Maximum risk per trade as percentage of account
• Max Daily Drawdown: Maximum allowed daily loss percentage
• Max Concurrent Trades: Maximum number of simultaneous trades
• Simulation Mode: Enable for paper trading
• Auto Trading: Enable automated trade execution

Broker Settings:
• Server Name: MT4 broker server name
• Account Type: Demo or live account
• EA Bridge Port: Communication port for EA bridge
• Timezone Offsets: Time zone adjustments

Advanced Settings:
• Database Path: Location of trading database file
• Backup on Start: Create database backup on startup
• Connection Timeout: Network timeout in seconds

Note: Some changes require restarting the application.
"""
        
        help_window = tk.Toplevel()
        help_window.title("Settings Help")
        help_window.geometry("600x500")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
    
    def refresh_data(self):
        """Refresh settings panel data"""
        logger.info("Refreshing settings panel data")
        self.check_for_changes()