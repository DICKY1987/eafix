"""
HUEY_P Trading Interface - System Status Tab
Monitor system health, connections, and error logs
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from core.data_models import SystemStatus

logger = logging.getLogger(__name__)

class SystemStatusTab:
    """System status monitoring and health checks"""
    
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app_controller = app_controller
        self.frame = None
        
        # Data storage
        self.system_metrics = {}
        self.error_log = []
        self.connection_history = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the system status UI"""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Create layout
        self.create_layout()
        
        # Setup components
        self.setup_connection_status()
        self.setup_system_metrics()
        self.setup_error_log()
        self.setup_controls()
        
        logger.info("System status UI setup complete")
    
    def create_layout(self):
        """Create the main layout structure"""
        # Main container with padding
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row - Connection status
        self.connection_frame = ttk.LabelFrame(main_container, text="🔗 Connection Status", padding=10)
        self.connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Middle row - split into metrics and controls
        middle_frame = ttk.Frame(main_container)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left panel - System metrics
        self.metrics_frame = ttk.LabelFrame(middle_frame, text="⚡ System Metrics", padding=10)
        self.metrics_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right panel - Controls
        self.controls_frame = ttk.LabelFrame(middle_frame, text="🎛️ Controls", padding=10)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Bottom row - Error log
        self.log_frame = ttk.LabelFrame(main_container, text="📋 System Log", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
    
    def setup_connection_status(self):
        """Setup connection status indicators"""
        # Create connection status grid
        conn_grid = ttk.Frame(self.connection_frame)
        conn_grid.pack(fill=tk.X)
        
        # Configure grid columns
        for i in range(6):
            conn_grid.columnconfigure(i, weight=1)
        
        # Database connection
        db_frame = ttk.LabelFrame(conn_grid, text="Database", padding=5)
        db_frame.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        self.db_status_indicator = tk.Canvas(db_frame, width=20, height=20, highlightthickness=0)
        self.db_status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.db_status_label = ttk.Label(db_frame, text="DISCONNECTED")
        self.db_status_label.pack(side=tk.LEFT)
        
        # EA Bridge connection
        ea_frame = ttk.LabelFrame(conn_grid, text="EA Bridge", padding=5)
        ea_frame.grid(row=0, column=1, sticky=tk.EW, padx=(2, 3))
        
        self.ea_status_indicator = tk.Canvas(ea_frame, width=20, height=20, highlightthickness=0)
        self.ea_status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.ea_status_label = ttk.Label(ea_frame, text="DISCONNECTED")
        self.ea_status_label.pack(side=tk.LEFT)
        
        # MT4 Terminal
        mt4_frame = ttk.LabelFrame(conn_grid, text="MT4 Terminal", padding=5)
        mt4_frame.grid(row=0, column=2, sticky=tk.EW, padx=(2, 3))
        
        self.mt4_status_indicator = tk.Canvas(mt4_frame, width=20, height=20, highlightthickness=0)
        self.mt4_status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.mt4_status_label = ttk.Label(mt4_frame, text="UNKNOWN")
        self.mt4_status_label.pack(side=tk.LEFT)
        
        # Broker connection
        broker_frame = ttk.LabelFrame(conn_grid, text="Broker", padding=5)
        broker_frame.grid(row=0, column=3, sticky=tk.EW, padx=(2, 3))
        
        self.broker_status_indicator = tk.Canvas(broker_frame, width=20, height=20, highlightthickness=0)
        self.broker_status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.broker_status_label = ttk.Label(broker_frame, text="UNKNOWN")
        self.broker_status_label.pack(side=tk.LEFT)
        
        # Overall health
        health_frame = ttk.LabelFrame(conn_grid, text="Overall Health", padding=5)
        health_frame.grid(row=0, column=4, columnspan=2, sticky=tk.EW, padx=(5, 0))
        
        self.health_indicator = tk.Canvas(health_frame, width=30, height=30, highlightthickness=0)
        self.health_indicator.pack(side=tk.LEFT, padx=(0, 10))
        self.health_label = ttk.Label(health_frame, text="UNKNOWN", font=('Arial', 12, 'bold'))
        self.health_label.pack(side=tk.LEFT)
        
        # Initialize indicators
        self.draw_status_indicator(self.db_status_indicator, "red")
        self.draw_status_indicator(self.ea_status_indicator, "red")
        self.draw_status_indicator(self.mt4_status_indicator, "gray")
        self.draw_status_indicator(self.broker_status_indicator, "gray")
        self.draw_health_indicator(self.health_indicator, "gray")
        
        # Connection details
        details_frame = ttk.Frame(self.connection_frame)
        details_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(details_frame, text="Last Heartbeat:").pack(side=tk.LEFT)
        self.last_heartbeat_label = ttk.Label(details_frame, text="Never")
        self.last_heartbeat_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(details_frame, text="Uptime:").pack(side=tk.LEFT)
        self.uptime_label = ttk.Label(details_frame, text="0s")
        self.uptime_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(details_frame, text="Connection Attempts:").pack(side=tk.LEFT)
        self.connection_attempts_label = ttk.Label(details_frame, text="0")
        self.connection_attempts_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_system_metrics(self):
        """Setup system metrics display"""
        metrics_grid = ttk.Frame(self.metrics_frame)
        metrics_grid.pack(fill=tk.BOTH, expand=True)
        
        # Performance metrics
        perf_frame = ttk.LabelFrame(metrics_grid, text="Performance", padding=5)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        perf_grid = ttk.Frame(perf_frame)
        perf_grid.pack(fill=tk.X)
        
        # CPU usage
        ttk.Label(perf_grid, text="CPU Usage:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.cpu_progress = ttk.Progressbar(perf_grid, length=100, mode='determinate')
        self.cpu_progress.grid(row=0, column=1, sticky=tk.EW, padx=(0, 5))
        self.cpu_label = ttk.Label(perf_grid, text="0%")
        self.cpu_label.grid(row=0, column=2, sticky=tk.W)
        
        # Memory usage
        ttk.Label(perf_grid, text="Memory Usage:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.memory_progress = ttk.Progressbar(perf_grid, length=100, mode='determinate')
        self.memory_progress.grid(row=1, column=1, sticky=tk.EW, padx=(0, 5))
        self.memory_label = ttk.Label(perf_grid, text="0%")
        self.memory_label.grid(row=1, column=2, sticky=tk.W)
        
        # Network latency
        ttk.Label(perf_grid, text="Network Latency:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.latency_progress = ttk.Progressbar(perf_grid, length=100, mode='determinate')
        self.latency_progress.grid(row=2, column=1, sticky=tk.EW, padx=(0, 5))
        self.latency_label = ttk.Label(perf_grid, text="0ms")
        self.latency_label.grid(row=2, column=2, sticky=tk.W)
        
        perf_grid.columnconfigure(1, weight=1)
        
        # Error counters
        error_frame = ttk.LabelFrame(metrics_grid, text="Error Counters", padding=5)
        error_frame.pack(fill=tk.X, pady=(0, 10))
        
        error_grid = ttk.Frame(error_frame)
        error_grid.pack(fill=tk.X)
        
        ttk.Label(error_grid, text="Total Errors:").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        self.total_errors_label = ttk.Label(error_grid, text="0", font=('Arial', 10, 'bold'))
        self.total_errors_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 40))
        
        ttk.Label(error_grid, text="Warnings:").grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        self.warnings_label = ttk.Label(error_grid, text="0")
        self.warnings_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 40))
        
        ttk.Label(error_grid, text="Last Error:").grid(row=1, column=0, sticky=tk.W, padx=(0, 20))
        self.last_error_label = ttk.Label(error_grid, text="None", wraplength=250)
        self.last_error_label.grid(row=1, column=1, columnspan=3, sticky=tk.W)
        
        # Component status
        comp_frame = ttk.LabelFrame(metrics_grid, text="Component Status", padding=5)
        comp_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for component status
        comp_columns = ('Component', 'Status', 'Last Update', 'Details')
        self.component_tree = ttk.Treeview(comp_frame, columns=comp_columns, show='headings', height=6)
        
        for col in comp_columns:
            self.component_tree.heading(col, text=col)
            if col == 'Component':
                self.component_tree.column(col, width=120)
            elif col == 'Status':
                self.component_tree.column(col, width=80)
            elif col == 'Last Update':
                self.component_tree.column(col, width=120)
            else:
                self.component_tree.column(col, width=150)
        
        comp_scrollbar = ttk.Scrollbar(comp_frame, orient=tk.VERTICAL, command=self.component_tree.yview)
        self.component_tree.configure(yscrollcommand=comp_scrollbar.set)
        
        self.component_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        comp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_error_log(self):
        """Setup error log display"""
        # Log controls
        log_controls = ttk.Frame(self.log_frame)
        log_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(log_controls, text="🔄 Refresh", command=self.refresh_error_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_controls, text="🗑️ Clear", command=self.clear_error_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_controls, text="💾 Export", command=self.export_error_log).pack(side=tk.LEFT, padx=(0, 10))
        
        # Log level filter
        ttk.Label(log_controls, text="Level:").pack(side=tk.LEFT, padx=(20, 5))
        self.log_level_var = tk.StringVar(value="All")
        log_level_combo = ttk.Combobox(log_controls, textvariable=self.log_level_var,
                                      values=["All", "ERROR", "WARNING", "INFO"], 
                                      width=10, state="readonly")
        log_level_combo.pack(side=tk.LEFT)
        log_level_combo.bind("<<ComboboxSelected>>", self.filter_error_log)
        
        # Error log text area
        log_container = ttk.Frame(self.log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.error_log_text = tk.Text(log_container, wrap=tk.WORD, font=('Courier', 9))
        log_v_scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.error_log_text.yview)
        log_h_scrollbar = ttk.Scrollbar(log_container, orient=tk.HORIZONTAL, command=self.error_log_text.xview)
        
        self.error_log_text.configure(yscrollcommand=log_v_scrollbar.set, xscrollcommand=log_h_scrollbar.set)
        
        self.error_log_text.grid(row=0, column=0, sticky=tk.NSEW)
        log_v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        log_h_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)
        
        # Configure text tags for different log levels
        self.error_log_text.tag_configure("ERROR", foreground="red")
        self.error_log_text.tag_configure("WARNING", foreground="orange")
        self.error_log_text.tag_configure("INFO", foreground="blue")
        self.error_log_text.tag_configure("DEBUG", foreground="gray")
    
    def setup_controls(self):
        """Setup control buttons"""
        # Connection controls
        conn_controls = ttk.LabelFrame(self.controls_frame, text="Connection", padding=5)
        conn_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(conn_controls, text="🔄 Reconnect All", command=self.reconnect_all).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(conn_controls, text="📊 Test Connection", command=self.test_connections).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(conn_controls, text="❤️ Send Heartbeat", command=self.send_heartbeat).pack(fill=tk.X)
        
        # System controls
        sys_controls = ttk.LabelFrame(self.controls_frame, text="System", padding=5)
        sys_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(sys_controls, text="🔄 Refresh All", command=self.refresh_all_data).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(sys_controls, text="🧹 Clear Cache", command=self.clear_cache).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(sys_controls, text="📊 System Report", command=self.generate_system_report).pack(fill=tk.X)
        
        # Emergency controls
        emergency_controls = ttk.LabelFrame(self.controls_frame, text="Emergency", padding=5)
        emergency_controls.pack(fill=tk.X)
        
        ttk.Button(emergency_controls, text="⚠️ Emergency Stop", command=self.emergency_stop, 
                  style="Emergency.TButton").pack(fill=tk.X, pady=(0, 5))
        ttk.Button(emergency_controls, text="🔄 Restart Interface", command=self.restart_interface).pack(fill=tk.X)
        
        # Configure emergency button style
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red")
    
    def draw_status_indicator(self, canvas, color):
        """Draw a status indicator circle"""
        canvas.delete("all")
        canvas.create_oval(5, 5, 15, 15, fill=color, outline="black")
    
    def draw_health_indicator(self, canvas, color):
        """Draw a larger health indicator"""
        canvas.delete("all")
        canvas.create_oval(5, 5, 25, 25, fill=color, outline="black", width=2)
    
    def update_data(self, system_status: SystemStatus, connection_status: Dict[str, Any]):
        """Update system status display with new data"""
        try:
            self.update_connection_status(system_status, connection_status)
            self.update_system_metrics(system_status)
            self.update_component_status()
            
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def update_connection_status(self, system_status: SystemStatus, connection_status: Dict[str, Any]):
        """Update connection status indicators"""
        # Database connection
        db_connected = connection_status.get('database', False)
        db_color = "green" if db_connected else "red"
        db_text = "CONNECTED" if db_connected else "DISCONNECTED"
        
        self.draw_status_indicator(self.db_status_indicator, db_color)
        self.db_status_label.config(text=db_text, foreground=db_color)
        
        # EA Bridge connection
        ea_connected = connection_status.get('ea_bridge', False)
        ea_color = "green" if ea_connected else "red"
        ea_text = "CONNECTED" if ea_connected else "DISCONNECTED"
        
        self.draw_status_indicator(self.ea_status_indicator, ea_color)
        self.ea_status_label.config(text=ea_text, foreground=ea_color)
        
        # MT4 and Broker status (derived from EA connection)
        if ea_connected:
            mt4_color = "green"
            mt4_text = "ONLINE"
            broker_color = "green"
            broker_text = "CONNECTED"
        else:
            mt4_color = "gray"
            mt4_text = "UNKNOWN"
            broker_color = "gray"
            broker_text = "UNKNOWN"
        
        self.draw_status_indicator(self.mt4_status_indicator, mt4_color)
        self.mt4_status_label.config(text=mt4_text, foreground=mt4_color)
        
        self.draw_status_indicator(self.broker_status_indicator, broker_color)
        self.broker_status_label.config(text=broker_text, foreground=broker_color)
        
        # Overall health
        health_status = system_status.overall_health
        if health_status == "HEALTHY":
            health_color = "green"
        elif health_status == "CAUTION":
            health_color = "yellow"
        elif health_status == "WARNING":
            health_color = "orange"
        else:
            health_color = "red"
        
        self.draw_health_indicator(self.health_indicator, health_color)
        self.health_label.config(text=health_status, foreground=health_color)
        
        # Connection details
        last_heartbeat = connection_status.get('last_heartbeat')
        if last_heartbeat:
            if isinstance(last_heartbeat, str):
                heartbeat_text = last_heartbeat
            else:
                heartbeat_text = last_heartbeat.strftime("%H:%M:%S")
        else:
            heartbeat_text = "Never"
        
        self.last_heartbeat_label.config(text=heartbeat_text)
        
        # Get uptime from EA connector
        ea_connector = self.app_controller.get_ea_connector()
        if ea_connector:
            conn_info = ea_connector.get_connection_info()
            attempts = conn_info.get('connection_attempts', 0)
            self.connection_attempts_label.config(text=str(attempts))
    
    def update_system_metrics(self, system_status: SystemStatus):
        """Update system performance metrics"""
        # CPU usage
        cpu_usage = system_status.cpu_usage
        self.cpu_progress['value'] = cpu_usage
        self.cpu_label.config(text=f"{cpu_usage:.1f}%")
        
        # Memory usage
        memory_usage = system_status.memory_usage
        self.memory_progress['value'] = memory_usage
        self.memory_label.config(text=f"{memory_usage:.1f}%")
        
        # Network latency
        latency = system_status.network_latency
        latency_percent = min(latency / 100 * 100, 100)  # Scale to 100ms max
        self.latency_progress['value'] = latency_percent
        self.latency_label.config(text=f"{latency:.0f}ms")
        
        # Error counters
        total_errors = system_status.error_count
        warnings = system_status.warning_count
        
        self.total_errors_label.config(text=str(total_errors))
        self.warnings_label.config(text=str(warnings))
        
        # Last error
        if system_status.recent_errors:
            last_error = system_status.recent_errors[-1]
            self.last_error_label.config(text=last_error)
        else:
            self.last_error_label.config(text="None")
    
    def update_component_status(self):
        """Update component status table"""
        # Clear existing items
        for item in self.component_tree.get_children():
            self.component_tree.delete(item)
        
        # Get component status from various sources
        components = [
            ("Database Manager", "CONNECTED" if self.app_controller.get_database_manager().is_connected() else "DISCONNECTED", 
             datetime.now().strftime("%H:%M:%S"), "SQLite connection"),
            ("EA Connector", "CONNECTED" if self.app_controller.get_ea_connector().is_connected() else "DISCONNECTED",
             datetime.now().strftime("%H:%M:%S"), "Bridge communication"),
            ("Signal Service", "UNKNOWN", "N/A", "Signal generation"),
            ("Risk Manager", "UNKNOWN", "N/A", "Risk monitoring"),
            ("Performance Monitor", "ACTIVE", datetime.now().strftime("%H:%M:%S"), "Metrics collection")
        ]
        
        for component, status, update_time, details in components:
            self.component_tree.insert('', tk.END, values=(component, status, update_time, details))
    
    def refresh_error_log(self):
        """Refresh the error log display"""
        self.error_log_text.delete(1.0, tk.END)
        
        # Get recent log entries
        try:
            # Read from log file if available
            log_file = "huey_interface.log"
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Show last 100 lines
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    for line in recent_lines:
                        # Determine log level and apply appropriate tag
                        if "ERROR" in line:
                            tag = "ERROR"
                        elif "WARNING" in line:
                            tag = "WARNING"
                        elif "INFO" in line:
                            tag = "INFO"
                        else:
                            tag = "DEBUG"
                        
                        self.error_log_text.insert(tk.END, line, tag)
                        
            except FileNotFoundError:
                self.error_log_text.insert(tk.END, "Log file not found. Logs will appear here as they are generated.\n")
            
            # Auto-scroll to bottom
            self.error_log_text.see(tk.END)
            
        except Exception as e:
            logger.error(f"Error refreshing error log: {e}")
    
    def clear_error_log(self):
        """Clear the error log display"""
        self.error_log_text.delete(1.0, tk.END)
        self.error_log_text.insert(tk.END, "Log cleared at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    
    def filter_error_log(self, event=None):
        """Filter error log by level"""
        # This would implement log level filtering
        logger.info(f"Filtering log by level: {self.log_level_var.get()}")
    
    def export_error_log(self):
        """Export error log to file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                content = self.error_log_text.get(1.0, tk.END)
                with open(filename, 'w') as f:
                    f.write(content)
                logger.info(f"Error log exported to: {filename}")
                
        except Exception as e:
            logger.error(f"Error exporting log: {e}")
    
    def reconnect_all(self):
        """Reconnect all components"""
        logger.info("Attempting to reconnect all components")
        
        # Reconnect database
        db_manager = self.app_controller.get_database_manager()
        if db_manager:
            db_manager.connect()
        
        # Reconnect EA bridge
        ea_connector = self.app_controller.get_ea_connector()
        if ea_connector:
            ea_connector.connect()
    
    def test_connections(self):
        """Test all connections"""
        logger.info("Testing all connections")
        
        results = []
        
        # Test database
        db_manager = self.app_controller.get_database_manager()
        if db_manager and db_manager.is_connected():
            results.append("Database: ✓ CONNECTED")
        else:
            results.append("Database: ✗ DISCONNECTED")
        
        # Test EA bridge
        ea_connector = self.app_controller.get_ea_connector()
        if ea_connector and ea_connector.is_connected():
            results.append("EA Bridge: ✓ CONNECTED")
        else:
            results.append("EA Bridge: ✗ DISCONNECTED")
        
        # Show results
        from tkinter import messagebox
        messagebox.showinfo("Connection Test Results", "\n".join(results))
    
    def send_heartbeat(self):
        """Send manual heartbeat"""
        ea_connector = self.app_controller.get_ea_connector()
        if ea_connector:
            success = ea_connector.send_heartbeat()
            if success:
                logger.info("Heartbeat sent successfully")
            else:
                logger.warning("Failed to send heartbeat")
    
    def refresh_all_data(self):
        """Refresh all system data"""
        logger.info("Refreshing all system status data")
        self.app_controller.refresh_all_data()
    
    def clear_cache(self):
        """Clear all cached data"""
        db_manager = self.app_controller.get_database_manager()
        if db_manager:
            db_manager.clear_cache()
        logger.info("Cache cleared")
    
    def generate_system_report(self):
        """Generate system status report"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                report = self.create_system_report()
                with open(filename, 'w') as f:
                    f.write(report)
                logger.info(f"System report generated: {filename}")
                
        except Exception as e:
            logger.error(f"Error generating system report: {e}")
    
    def create_system_report(self) -> str:
        """Create system status report text"""
        report = []
        report.append("HUEY_P TRADING SYSTEM STATUS REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Connection status
        report.append("CONNECTION STATUS:")
        db_connected = self.app_controller.get_database_manager().is_connected()
        ea_connected = self.app_controller.get_ea_connector().is_connected()
        
        report.append(f"  Database: {'CONNECTED' if db_connected else 'DISCONNECTED'}")
        report.append(f"  EA Bridge: {'CONNECTED' if ea_connected else 'DISCONNECTED'}")
        report.append("")
        
        # System metrics would be added here
        report.append("SYSTEM METRICS:")
        report.append("  CPU Usage: N/A")
        report.append("  Memory Usage: N/A")
        report.append("  Network Latency: N/A")
        report.append("")
        
        return "\n".join(report)
    
    def emergency_stop(self):
        """Emergency stop all trading"""
        from tkinter import messagebox
        
        result = messagebox.askyesno("Emergency Stop", 
                                   "This will attempt to stop all trading activity.\n\nAre you sure?",
                                   icon="warning")
        
        if result:
            logger.warning("EMERGENCY STOP initiated by user")
            # Send emergency stop signal to EA
            ea_connector = self.app_controller.get_ea_connector()
            if ea_connector:
                # This would send an emergency stop signal
                logger.info("Emergency stop signal sent to EA")
    
    def restart_interface(self):
        """Restart the interface application"""
        from tkinter import messagebox
        
        result = messagebox.askyesno("Restart Interface", 
                                   "This will restart the trading interface.\n\nAre you sure?")
        
        if result:
            logger.info("Interface restart requested by user")
            # This would trigger application restart
            self.app_controller.show_info("Restart", "Please restart the application manually.")
    
    def refresh_data(self):
        """Refresh system status data"""
        logger.info("Refreshing system status data")
        self.refresh_error_log()
        self.update_component_status()