"""
Configuration Management System for DDE Price Import Interface
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import copy


@dataclass
class DDEConfig:
    """DDE connection configuration"""
    server_name: str = "MT4"
    update_interval: float = 0.1
    max_reconnect_attempts: int = 10
    reconnect_interval: float = 5.0
    connection_timeout: float = 30.0


@dataclass
class PriceConfig:
    """Price data management configuration"""
    buffer_size: int = 1000
    max_symbols: int = 50
    data_validation: bool = True
    auto_cleanup: bool = True
    cleanup_interval_hours: int = 1


@dataclass
class UIConfig:
    """User interface configuration"""
    refresh_rate_ms: int = 500
    theme: str = "default"
    window_width: int = 1200
    window_height: int = 800
    auto_save_layout: bool = True
    chart_max_points: int = 200


@dataclass
class IndicatorConfig:
    """Individual indicator configuration"""
    name: str
    type: str
    parameters: Dict[str, Any]
    enabled: bool = True
    symbol: str = ""


@dataclass
class SystemConfig:
    """Overall system configuration"""
    dde: DDEConfig
    price: PriceConfig
    ui: UIConfig
    default_symbols: List[str]
    indicator_presets: Dict[str, Dict[str, Any]]
    logging_level: str = "INFO"
    auto_start_monitoring: bool = False
    performance_monitoring: bool = True


class ConfigurationManager:
    """Manages application configuration with validation and persistence"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "settings.json")
        self.backup_file = os.path.join(config_dir, "settings_backup.json")
        self.user_config_file = os.path.join(config_dir, "user_settings.json")
        
        self.logger = logging.getLogger(__name__)
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load configuration
        self.config = self._load_configuration()
        self.user_config = self._load_user_configuration()
        
        # Track changes for auto-save
        self._config_changed = False
        self._last_save = datetime.now()
    
    def _get_default_config(self) -> SystemConfig:
        """Get default system configuration"""
        return SystemConfig(
            dde=DDEConfig(),
            price=PriceConfig(),
            ui=UIConfig(),
            default_symbols=[
                "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD",
                "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP"
            ],
            indicator_presets={
                "sma_20": {"type": "SMA", "period": 20},
                "sma_50": {"type": "SMA", "period": 50},
                "ema_12": {"type": "EMA", "period": 12},
                "ema_26": {"type": "EMA", "period": 26},
                "rsi_14": {"type": "RSI", "period": 14},
                "macd_standard": {
                    "type": "MACD", 
                    "fast_period": 12, 
                    "slow_period": 26, 
                    "signal_period": 9
                },
                "bb_20": {"type": "BollingerBands", "period": 20, "std_dev": 2.0},
                "atr_14": {"type": "ATR", "period": 14},
                "stoch_14": {"type": "Stochastic", "k_period": 14, "d_period": 3}
            }
        )
    
    def _load_configuration(self) -> SystemConfig:
        """Load main system configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Convert dict to SystemConfig
                config = self._dict_to_config(data)
                self.logger.info("Loaded configuration from file")
                return config
            else:
                self.logger.info("No configuration file found, using defaults")
                return self._get_default_config()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            
            # Try backup
            if os.path.exists(self.backup_file):
                try:
                    with open(self.backup_file, 'r') as f:
                        data = json.load(f)
                    config = self._dict_to_config(data)
                    self.logger.info("Loaded configuration from backup")
                    return config
                except Exception as backup_error:
                    self.logger.error(f"Error loading backup: {backup_error}")
            
            # Fall back to defaults
            self.logger.info("Using default configuration")
            return self._get_default_config()
    
    def _load_user_configuration(self) -> Dict:
        """Load user-specific configuration"""
        try:
            if os.path.exists(self.user_config_file):
                with open(self.user_config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading user configuration: {e}")
            return {}
    
    def _dict_to_config(self, data: Dict) -> SystemConfig:
        """Convert dictionary to SystemConfig with validation"""
        try:
            # Handle nested objects
            dde_data = data.get('dde', {})
            price_data = data.get('price', {})
            ui_data = data.get('ui', {})
            
            return SystemConfig(
                dde=DDEConfig(**dde_data) if dde_data else DDEConfig(),
                price=PriceConfig(**price_data) if price_data else PriceConfig(),
                ui=UIConfig(**ui_data) if ui_data else UIConfig(),
                default_symbols=data.get('default_symbols', []),
                indicator_presets=data.get('indicator_presets', {}),
                logging_level=data.get('logging_level', 'INFO'),
                auto_start_monitoring=data.get('auto_start_monitoring', False),
                performance_monitoring=data.get('performance_monitoring', True)
            )
        except Exception as e:
            self.logger.error(f"Error converting dict to config: {e}")
            # Return default if conversion fails
            return self._get_default_config()
    
    def save_configuration(self, backup: bool = True) -> bool:
        """Save current configuration to file"""
        try:
            # Create backup if requested
            if backup and os.path.exists(self.config_file):
                import shutil
                shutil.copy2(self.config_file, self.backup_file)
            
            # Convert config to dict
            config_dict = asdict(self.config)
            
            # Add metadata
            config_dict['_metadata'] = {
                'saved_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'saved_by': 'ConfigurationManager'
            }
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, sort_keys=True)
            
            self._config_changed = False
            self._last_save = datetime.now()
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def save_user_configuration(self) -> bool:
        """Save user-specific configuration"""
        try:
            with open(self.user_config_file, 'w') as f:
                json.dump(self.user_config, f, indent=2)
            
            self.logger.info("User configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving user configuration: {e}")
            return False
    
    def get_dde_config(self) -> DDEConfig:
        """Get DDE configuration"""
        return self.config.dde
    
    def get_price_config(self) -> PriceConfig:
        """Get price management configuration"""
        return self.config.price
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        return self.config.ui
    
    def get_default_symbols(self) -> List[str]:
        """Get default symbols list"""
        return self.config.default_symbols.copy()
    
    def get_indicator_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get indicator presets"""
        return copy.deepcopy(self.config.indicator_presets)
    
    def update_dde_config(self, **kwargs) -> bool:
        """Update DDE configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.dde, key):
                    setattr(self.config.dde, key, value)
                    self._config_changed = True
                else:
                    self.logger.warning(f"Unknown DDE config parameter: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating DDE config: {e}")
            return False
    
    def update_price_config(self, **kwargs) -> bool:
        """Update price management configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.price, key):
                    setattr(self.config.price, key, value)
                    self._config_changed = True
                else:
                    self.logger.warning(f"Unknown price config parameter: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating price config: {e}")
            return False
    
    def update_ui_config(self, **kwargs) -> bool:
        """Update UI configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config.ui, key):
                    setattr(self.config.ui, key, value)
                    self._config_changed = True
                else:
                    self.logger.warning(f"Unknown UI config parameter: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating UI config: {e}")
            return False
    
    def add_symbol_to_defaults(self, symbol: str) -> bool:
        """Add symbol to default list"""
        try:
            if symbol not in self.config.default_symbols:
                self.config.default_symbols.append(symbol.upper())
                self._config_changed = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error adding symbol {symbol}: {e}")
            return False
    
    def remove_symbol_from_defaults(self, symbol: str) -> bool:
        """Remove symbol from default list"""
        try:
            if symbol in self.config.default_symbols:
                self.config.default_symbols.remove(symbol)
                self._config_changed = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing symbol {symbol}: {e}")
            return False
    
    def add_indicator_preset(self, name: str, preset: Dict[str, Any]) -> bool:
        """Add indicator preset"""
        try:
            self.config.indicator_presets[name] = preset.copy()
            self._config_changed = True
            return True
        except Exception as e:
            self.logger.error(f"Error adding indicator preset {name}: {e}")
            return False
    
    def remove_indicator_preset(self, name: str) -> bool:
        """Remove indicator preset"""
        try:
            if name in self.config.indicator_presets:
                del self.config.indicator_presets[name]
                self._config_changed = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing indicator preset {name}: {e}")
            return False
    
    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return list of issues"""
        issues = []
        
        try:
            # Validate DDE config
            if self.config.dde.update_interval <= 0:
                issues.append("DDE update interval must be positive")
            
            if self.config.dde.max_reconnect_attempts < 0:
                issues.append("DDE max reconnect attempts must be non-negative")
            
            # Validate price config
            if self.config.price.buffer_size < 10:
                issues.append("Price buffer size too small (minimum 10)")
            
            if self.config.price.buffer_size > 100000:
                issues.append("Price buffer size too large (maximum 100000)")
            
            if self.config.price.max_symbols < 1:
                issues.append("Max symbols must be at least 1")
            
            # Validate UI config
            if self.config.ui.refresh_rate_ms < 100:
                issues.append("UI refresh rate too fast (minimum 100ms)")
            
            if self.config.ui.refresh_rate_ms > 10000:
                issues.append("UI refresh rate too slow (maximum 10s)")
            
            # Validate symbols
            for symbol in self.config.default_symbols:
                if not isinstance(symbol, str) or len(symbol) < 3:
                    issues.append(f"Invalid symbol format: {symbol}")
            
            # Validate indicator presets
            required_indicator_fields = ['type']
            for name, preset in self.config.indicator_presets.items():
                for field in required_indicator_fields:
                    if field not in preset:
                        issues.append(f"Indicator preset '{name}' missing required field: {field}")
            
        except Exception as e:
            issues.append(f"Configuration validation error: {e}")
        
        return issues
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = self._get_default_config()
            self._config_changed = True
            self.logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False
    
    def export_configuration(self, filename: str) -> bool:
        """Export configuration to specified file"""
        try:
            config_dict = asdict(self.config)
            config_dict['_export_info'] = {
                'exported_at': datetime.now().isoformat(),
                'exported_from': 'ConfigurationManager'
            }
            
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuration exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration to {filename}: {e}")
            return False
    
    def import_configuration(self, filename: str, validate: bool = True) -> bool:
        """Import configuration from specified file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Remove metadata
            data.pop('_metadata', None)
            data.pop('_export_info', None)
            
            # Convert to config object
            new_config = self._dict_to_config(data)
            
            # Validate if requested
            if validate:
                # Temporarily set new config for validation
                old_config = self.config
                self.config = new_config
                issues = self.validate_configuration()
                
                if issues:
                    self.config = old_config  # Restore old config
                    self.logger.error(f"Configuration validation failed: {issues}")
                    return False
            
            # Apply new configuration
            self.config = new_config
            self._config_changed = True
            
            self.logger.info(f"Configuration imported from {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing configuration from {filename}: {e}")
            return False
    
    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """Get user-specific setting"""
        return self.user_config.get(key, default)
    
    def set_user_setting(self, key: str, value: Any) -> bool:
        """Set user-specific setting"""
        try:
            self.user_config[key] = value
            return self.save_user_configuration()
        except Exception as e:
            self.logger.error(f"Error setting user setting {key}: {e}")
            return False
    
    def get_configuration_info(self) -> Dict:
        """Get configuration information"""
        return {
            'config_file': self.config_file,
            'backup_file': self.backup_file,
            'user_config_file': self.user_config_file,
            'config_changed': self._config_changed,
            'last_save': self._last_save.isoformat(),
            'validation_issues': self.validate_configuration()
        }
    
    def auto_save_if_needed(self, force_interval_minutes: int = 5) -> bool:
        """Auto-save configuration if changes detected and enough time passed"""
        if not self._config_changed:
            return False
        
        time_since_save = datetime.now() - self._last_save
        if time_since_save.total_seconds() >= (force_interval_minutes * 60):
            return self.save_configuration()
        
        return False


class ConfigurationDialog:
    """GUI dialog for editing configuration"""
    
    def __init__(self, parent, config_manager: ConfigurationManager):
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        self.parent = parent
        self.config_manager = config_manager
        self.result = False
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuration Settings")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_current_values()
        self._center_window()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        import tkinter as tk
        from tkinter import ttk
        
        # Create notebook for different config sections
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # DDE Configuration tab
        self.dde_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dde_frame, text="DDE Settings")
        self._create_dde_widgets()
        
        # Price Configuration tab
        self.price_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.price_frame, text="Price Settings")
        self._create_price_widgets()
        
        # UI Configuration tab
        self.ui_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ui_frame, text="UI Settings")
        self._create_ui_widgets()
        
        # Symbols tab
        self.symbols_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.symbols_frame, text="Default Symbols")
        self._create_symbols_widgets()
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Apply", command=self._apply).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side='right')
    
    def _create_dde_widgets(self):
        """Create DDE configuration widgets"""
        import tkinter as tk
        from tkinter import ttk
        
        # Server name
        ttk.Label(self.dde_frame, text="Server Name:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.server_name_var = tk.StringVar()
        ttk.Entry(self.dde_frame, textvariable=self.server_name_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        # Update interval
        ttk.Label(self.dde_frame, text="Update Interval (s):").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.update_interval_var = tk.StringVar()
        ttk.Entry(self.dde_frame, textvariable=self.update_interval_var, width=20).grid(row=1, column=1, padx=5, pady=2)
        
        # Max reconnect attempts
        ttk.Label(self.dde_frame, text="Max Reconnect Attempts:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.max_reconnect_var = tk.StringVar()
        ttk.Entry(self.dde_frame, textvariable=self.max_reconnect_var, width=20).grid(row=2, column=1, padx=5, pady=2)
    
    def _create_price_widgets(self):
        """Create price configuration widgets"""
        import tkinter as tk
        from tkinter import ttk
        
        # Buffer size
        ttk.Label(self.price_frame, text="Buffer Size:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.buffer_size_var = tk.StringVar()
        ttk.Entry(self.price_frame, textvariable=self.buffer_size_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        # Max symbols
        ttk.Label(self.price_frame, text="Max Symbols:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.max_symbols_var = tk.StringVar()
        ttk.Entry(self.price_frame, textvariable=self.max_symbols_var, width=20).grid(row=1, column=1, padx=5, pady=2)
        
        # Data validation
        self.data_validation_var = tk.BooleanVar()
        ttk.Checkbutton(self.price_frame, text="Enable Data Validation", 
                       variable=self.data_validation_var).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=2)
    
    def _create_ui_widgets(self):
        """Create UI configuration widgets"""
        import tkinter as tk
        from tkinter import ttk
        
        # Refresh rate
        ttk.Label(self.ui_frame, text="Refresh Rate (ms):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.refresh_rate_var = tk.StringVar()
        ttk.Entry(self.ui_frame, textvariable=self.refresh_rate_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        # Window size
        ttk.Label(self.ui_frame, text="Window Width:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.window_width_var = tk.StringVar()
        ttk.Entry(self.ui_frame, textvariable=self.window_width_var, width=20).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(self.ui_frame, text="Window Height:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.window_height_var = tk.StringVar()
        ttk.Entry(self.ui_frame, textvariable=self.window_height_var, width=20).grid(row=2, column=1, padx=5, pady=2)
    
    def _create_symbols_widgets(self):
        """Create symbols configuration widgets"""
        import tkinter as tk
        from tkinter import ttk
        
        # Symbol list
        ttk.Label(self.symbols_frame, text="Default Symbols:").pack(anchor='w', padx=5, pady=2)
        
        listbox_frame = ttk.Frame(self.symbols_frame)
        listbox_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        self.symbols_listbox = tk.Listbox(listbox_frame)
        symbols_scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.symbols_listbox.yview)
        self.symbols_listbox.config(yscrollcommand=symbols_scrollbar.set)
        
        self.symbols_listbox.pack(side='left', fill='both', expand=True)
        symbols_scrollbar.pack(side='right', fill='y')
    
    def _load_current_values(self):
        """Load current configuration values into dialog"""
        config = self.config_manager.config
        
        # DDE settings
        self.server_name_var.set(config.dde.server_name)
        self.update_interval_var.set(str(config.dde.update_interval))
        self.max_reconnect_var.set(str(config.dde.max_reconnect_attempts))
        
        # Price settings
        self.buffer_size_var.set(str(config.price.buffer_size))
        self.max_symbols_var.set(str(config.price.max_symbols))
        self.data_validation_var.set(config.price.data_validation)
        
        # UI settings
        self.refresh_rate_var.set(str(config.ui.refresh_rate_ms))
        self.window_width_var.set(str(config.ui.window_width))
        self.window_height_var.set(str(config.ui.window_height))
        
        # Symbols
        for symbol in config.default_symbols:
            self.symbols_listbox.insert('end', symbol)
    
    def _center_window(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _apply(self):
        """Apply configuration changes"""
        try:
            # Update DDE config
            self.config_manager.update_dde_config(
                server_name=self.server_name_var.get(),
                update_interval=float(self.update_interval_var.get()),
                max_reconnect_attempts=int(self.max_reconnect_var.get())
            )
            
            # Update price config
            self.config_manager.update_price_config(
                buffer_size=int(self.buffer_size_var.get()),
                max_symbols=int(self.max_symbols_var.get()),
                data_validation=self.data_validation_var.get()
            )
            
            # Update UI config
            self.config_manager.update_ui_config(
                refresh_rate_ms=int(self.refresh_rate_var.get()),
                window_width=int(self.window_width_var.get()),
                window_height=int(self.window_height_var.get())
            )
            
            # Validate configuration
            issues = self.config_manager.validate_configuration()
            if issues:
                from tkinter import messagebox
                messagebox.showerror("Validation Error", "\n".join(issues))
                return False
            
            # Save configuration
            if self.config_manager.save_configuration():
                self.result = True
                return True
            else:
                from tkinter import messagebox
                messagebox.showerror("Save Error", "Failed to save configuration")
                return False
                
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Invalid Input", f"Please check your input values:\n{e}")
            return False
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Error applying configuration:\n{e}")
            return False
    
    def _ok(self):
        """OK button handler"""
        if self._apply():
            self.dialog.destroy()
    
    def _cancel(self):
        """Cancel button handler"""
        self.dialog.destroy()


if __name__ == "__main__":
    # Example usage
    config_manager = ConfigurationManager()
    
    print("Configuration loaded:")
    print(f"DDE Server: {config_manager.get_dde_config().server_name}")
    print(f"Buffer Size: {config_manager.get_price_config().buffer_size}")
    print(f"Default Symbols: {config_manager.get_default_symbols()}")
    
    # Validate configuration
    issues = config_manager.validate_configuration()
    if issues:
        print(f"Configuration issues: {issues}")
    else:
        print("Configuration is valid")
    
    # Test configuration updates
    config_manager.update_dde_config(update_interval=0.2)
    config_manager.add_symbol_to_defaults("EURAUD")
    
    # Save configuration
    if config_manager.save_configuration():
        print("Configuration saved successfully")
    
    # Export configuration
    if config_manager.export_configuration("test_export.json"):
        print("Configuration exported successfully")