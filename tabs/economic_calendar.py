"""
HUEY_P Trading Interface - Economic Calendar Tab
Economic calendar display and news event filtering functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import csv
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class NewsEvent:
    """Data structure for economic news events"""
    
    def __init__(self, date_time: datetime, currency: str, event: str, 
                 importance: str, previous: str = "", forecast: str = "", 
                 actual: str = "", comment: str = ""):
        self.date_time = date_time
        self.currency = currency
        self.event = event
        self.importance = importance  # Low, Medium, High
        self.previous = previous
        self.forecast = forecast
        self.actual = actual
        self.comment = comment
    
    @property
    def impact_color(self) -> str:
        """Get color based on importance level"""
        if self.importance.upper() == "HIGH":
            return "red"
        elif self.importance.upper() == "MEDIUM":
            return "orange"
        else:
            return "gray"
    
    @property
    def is_today(self) -> bool:
        """Check if event is today"""
        return self.date_time.date() == date.today()
    
    @property
    def is_upcoming(self) -> bool:
        """Check if event is in the future"""
        return self.date_time > datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'date_time': self.date_time.isoformat(),
            'currency': self.currency,
            'event': self.event,
            'importance': self.importance,
            'previous': self.previous,
            'forecast': self.forecast,
            'actual': self.actual,
            'comment': self.comment
        }

class EconomicCalendar:
    """Economic calendar tab for news events display and management"""
    
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app_controller = app_controller
        self.frame = None
        
        # Data storage
        self.news_events = []  # List of NewsEvent objects
        self.filtered_events = []
        self.csv_file_path = ""
        
        # Filter settings
        self.date_filter = "today"  # today, this_week, all
        self.currency_filter = "all"  # all, USD, EUR, GBP, etc.
        self.importance_filter = "all"  # all, high, medium, low
        
        # UI components
        self.calendar_tree = None
        self.status_label = None
        self.filter_frame = None
        self.date_var = tk.StringVar(value=self.date_filter)
        self.currency_var = tk.StringVar(value=self.currency_filter)
        self.importance_var = tk.StringVar(value=self.importance_filter)
        
        self.setup_ui()
        self.load_default_calendar()
    
    def setup_ui(self):
        """Setup the economic calendar UI"""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Create layout
        self.create_layout()
        
        # Setup components
        self.setup_toolbar()
        self.setup_filter_section()
        self.setup_calendar_display()
        self.setup_status_bar()
        
        logger.info("Economic calendar UI setup complete")
    
    def create_layout(self):
        """Create the main layout structure"""
        # Main container with padding
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar at top
        self.toolbar_frame = ttk.Frame(main_container)
        self.toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter section
        self.filter_frame = ttk.LabelFrame(main_container, text="🔍 Filters", padding=10)
        self.filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Calendar display (main content)
        self.calendar_frame = ttk.LabelFrame(main_container, text="📅 Economic Calendar", padding=10)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Status bar at bottom
        self.status_frame = ttk.Frame(main_container)
        self.status_frame.pack(fill=tk.X)
    
    def setup_toolbar(self):
        """Setup the toolbar with action buttons"""
        # Load CSV button
        load_btn = ttk.Button(self.toolbar_frame, text="📂 Load CSV", command=self.load_csv_file)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Reload button
        reload_btn = ttk.Button(self.toolbar_frame, text="🔄 Reload", command=self.reload_calendar)
        reload_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Export button
        export_btn = ttk.Button(self.toolbar_frame, text="💾 Export", command=self.export_calendar)
        export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Add Event button
        add_btn = ttk.Button(self.toolbar_frame, text="➕ Add Event", command=self.add_event_dialog)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Remove Event button
        remove_btn = ttk.Button(self.toolbar_frame, text="➖ Remove Event", command=self.remove_selected_event)
        remove_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Spacer
        spacer = ttk.Frame(self.toolbar_frame)
        spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Current file label
        self.file_label = ttk.Label(self.toolbar_frame, text="No file loaded", foreground="gray")
        self.file_label.pack(side=tk.RIGHT)
    
    def setup_filter_section(self):
        """Setup the filter controls"""
        # Date filter
        ttk.Label(self.filter_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        date_combo = ttk.Combobox(self.filter_frame, textvariable=self.date_var, 
                                 values=["today", "this_week", "this_month", "all"],
                                 state="readonly", width=12)
        date_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        date_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Currency filter
        ttk.Label(self.filter_frame, text="Currency:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        currency_combo = ttk.Combobox(self.filter_frame, textvariable=self.currency_var,
                                     values=["all", "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"],
                                     state="readonly", width=8)
        currency_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        currency_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Importance filter
        ttk.Label(self.filter_frame, text="Importance:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        importance_combo = ttk.Combobox(self.filter_frame, textvariable=self.importance_var,
                                       values=["all", "high", "medium", "low"],
                                       state="readonly", width=10)
        importance_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        importance_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Search box
        ttk.Label(self.filter_frame, text="Search:").grid(row=0, column=6, sticky=tk.W, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(self.filter_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=7, sticky=tk.W, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.apply_filters)
        
        # Clear filters button
        clear_btn = ttk.Button(self.filter_frame, text="Clear", command=self.clear_filters)
        clear_btn.grid(row=0, column=8, sticky=tk.W)
    
    def setup_calendar_display(self):
        """Setup the main calendar display treeview"""
        # Create treeview with columns
        columns = ('Time', 'Currency', 'Event', 'Importance', 'Previous', 'Forecast', 'Actual')
        self.calendar_tree = ttk.Treeview(self.calendar_frame, columns=columns, show='headings', height=15)
        
        # Configure column headers and widths
        self.calendar_tree.heading('Time', text='Time')
        self.calendar_tree.column('Time', width=120, minwidth=100)
        
        self.calendar_tree.heading('Currency', text='Currency')
        self.calendar_tree.column('Currency', width=70, minwidth=60)
        
        self.calendar_tree.heading('Event', text='Event')
        self.calendar_tree.column('Event', width=250, minwidth=200)
        
        self.calendar_tree.heading('Importance', text='Impact')
        self.calendar_tree.column('Importance', width=80, minwidth=70)
        
        self.calendar_tree.heading('Previous', text='Previous')
        self.calendar_tree.column('Previous', width=80, minwidth=70)
        
        self.calendar_tree.heading('Forecast', text='Forecast')
        self.calendar_tree.column('Forecast', width=80, minwidth=70)
        
        self.calendar_tree.heading('Actual', text='Actual')
        self.calendar_tree.column('Actual', width=80, minwidth=70)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(self.calendar_frame, orient=tk.VERTICAL, command=self.calendar_tree.yview)
        h_scrollbar = ttk.Scrollbar(self.calendar_frame, orient=tk.HORIZONTAL, command=self.calendar_tree.xview)
        
        self.calendar_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.calendar_tree.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        # Configure grid weights
        self.calendar_frame.grid_rowconfigure(0, weight=1)
        self.calendar_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click event
        self.calendar_tree.bind('<Double-1>', self.on_event_double_click)
        
        # Context menu
        self.setup_context_menu()
    
    def setup_context_menu(self):
        """Setup right-click context menu"""
        self.context_menu = tk.Menu(self.calendar_tree, tearoff=0)
        self.context_menu.add_command(label="Edit Event", command=self.edit_selected_event)
        self.context_menu.add_command(label="Remove Event", command=self.remove_selected_event)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Event Details", command=self.copy_event_details)
        
        self.calendar_tree.bind('<Button-3>', self.show_context_menu)
    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_label = ttk.Label(self.status_frame, text="Ready", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        # Event count label
        self.count_label = ttk.Label(self.status_frame, text="Events: 0")
        self.count_label.pack(side=tk.RIGHT)
    
    def load_csv_file(self):
        """Load economic calendar from CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Economic Calendar CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            defaultextension=".csv"
        )
        
        if file_path:
            try:
                self.csv_file_path = file_path
                self.load_events_from_csv(file_path)
                self.file_label.config(text=f"File: {Path(file_path).name}")
                self.status_label.config(text=f"Loaded {len(self.news_events)} events", foreground="green")
                logger.info(f"Loaded economic calendar from: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file:\n{str(e)}")
                logger.error(f"Error loading CSV file: {e}")
    
    def load_events_from_csv(self, file_path: str):
        """Load events from CSV file"""
        self.news_events.clear()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse datetime - adjust format as needed
                    date_str = row.get('Date', '') + ' ' + row.get('Time', '00:00')
                    event_datetime = datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M')
                    
                    event = NewsEvent(
                        date_time=event_datetime,
                        currency=row.get('Currency', ''),
                        event=row.get('Event', ''),
                        importance=row.get('Importance', 'Low'),
                        previous=row.get('Previous', ''),
                        forecast=row.get('Forecast', ''),
                        actual=row.get('Actual', ''),
                        comment=row.get('Comment', '')
                    )
                    self.news_events.append(event)
                    
                except ValueError as e:
                    logger.warning(f"Skipping invalid date/time in row: {row}. Error: {e}")
                    continue
        
        self.apply_filters()
    
    def load_default_calendar(self):
        """Load default economic calendar data"""
        # Check for NewsCalendar.csv in MT4 Files folder (as mentioned in docs)
        mt4_files_path = Path.cwd() / "Files" / "NewsCalendar.csv"
        
        if mt4_files_path.exists():
            try:
                self.csv_file_path = str(mt4_files_path)
                self.load_events_from_csv(str(mt4_files_path))
                self.file_label.config(text="File: NewsCalendar.csv")
                logger.info(f"Loaded default economic calendar from: {mt4_files_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load default calendar: {e}")
        
        # Load sample data if no file found
        self.load_sample_data()
    
    def load_sample_data(self):
        """Load sample economic calendar data for demonstration"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        sample_events = [
            NewsEvent(today + timedelta(hours=8, minutes=30), "USD", "NFP - Non-Farm Payrolls", "High", "150K", "175K", "", "Major employment indicator"),
            NewsEvent(today + timedelta(hours=10), "USD", "Unemployment Rate", "High", "4.1%", "4.0%", "", "Key labor market data"),
            NewsEvent(today + timedelta(hours=14), "EUR", "ECB Interest Rate Decision", "High", "4.50%", "4.50%", "", "Central bank policy"),
            NewsEvent(today + timedelta(days=1, hours=9), "GBP", "GDP Growth Rate", "Medium", "0.2%", "0.3%", "", "Economic growth measure"),
            NewsEvent(today + timedelta(days=1, hours=15), "USD", "FOMC Meeting Minutes", "High", "", "", "", "Federal Reserve policy insights"),
            NewsEvent(today + timedelta(days=2, hours=7), "JPY", "Bank of Japan Rate Decision", "High", "-0.10%", "-0.10%", "", "BoJ monetary policy"),
            NewsEvent(today + timedelta(days=2, hours=12), "EUR", "Inflation Rate", "Medium", "2.8%", "2.9%", "", "Price stability indicator"),
        ]
        
        self.news_events = sample_events
        self.apply_filters()
        self.status_label.config(text="Sample data loaded", foreground="blue")
        self.file_label.config(text="Sample Data")
        logger.info("Loaded sample economic calendar data")
    
    def apply_filters(self, event=None):
        """Apply current filters to the news events"""
        self.filtered_events = []
        
        for news_event in self.news_events:
            # Date filter
            if self.date_var.get() == "today" and not news_event.is_today:
                continue
            elif self.date_var.get() == "this_week":
                week_start = date.today() - timedelta(days=date.today().weekday())
                week_end = week_start + timedelta(days=6)
                if not (week_start <= news_event.date_time.date() <= week_end):
                    continue
            elif self.date_var.get() == "this_month":
                if news_event.date_time.month != date.today().month:
                    continue
            
            # Currency filter
            if self.currency_var.get() != "all" and news_event.currency != self.currency_var.get():
                continue
            
            # Importance filter
            if self.importance_var.get() != "all" and news_event.importance.lower() != self.importance_var.get():
                continue
            
            # Search filter
            search_text = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
            if search_text and search_text not in news_event.event.lower():
                continue
            
            self.filtered_events.append(news_event)
        
        self.refresh_calendar_display()
    
    def refresh_calendar_display(self):
        """Refresh the calendar display with filtered events"""
        # Clear existing items
        for item in self.calendar_tree.get_children():
            self.calendar_tree.delete(item)
        
        # Sort events by date/time
        sorted_events = sorted(self.filtered_events, key=lambda x: x.date_time)
        
        # Insert filtered events
        for event in sorted_events:
            # Format time display
            time_str = event.date_time.strftime("%m/%d %H:%M")
            
            # Insert row
            item = self.calendar_tree.insert('', tk.END, values=(
                time_str,
                event.currency,
                event.event,
                event.importance,
                event.previous,
                event.forecast,
                event.actual
            ))
            
            # Apply color coding based on importance
            if event.importance.upper() == "HIGH":
                self.calendar_tree.set(item, 'Importance', f"🔴 {event.importance}")
            elif event.importance.upper() == "MEDIUM":
                self.calendar_tree.set(item, 'Importance', f"🟡 {event.importance}")
            else:
                self.calendar_tree.set(item, 'Importance', f"⚪ {event.importance}")
            
            # Highlight past events differently
            if not event.is_upcoming:
                self.calendar_tree.item(item, tags=('past',))
        
        # Configure tags for styling
        self.calendar_tree.tag_configure('past', background='#f0f0f0')
        
        # Update count
        self.count_label.config(text=f"Events: {len(self.filtered_events)}")
    
    def clear_filters(self):
        """Clear all filters and show all events"""
        self.date_var.set("all")
        self.currency_var.set("all")
        self.importance_var.set("all")
        if hasattr(self, 'search_var'):
            self.search_var.set("")
        self.apply_filters()
    
    def reload_calendar(self):
        """Reload the calendar from the current CSV file"""
        if self.csv_file_path and os.path.exists(self.csv_file_path):
            try:
                self.load_events_from_csv(self.csv_file_path)
                self.status_label.config(text="Calendar reloaded", foreground="green")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reload calendar:\n{str(e)}")
        else:
            self.load_sample_data()
    
    def export_calendar(self):
        """Export current filtered events to CSV"""
        if not self.filtered_events:
            messagebox.showwarning("Warning", "No events to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Economic Calendar",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Write header
                    writer.writerow(['Date', 'Time', 'Currency', 'Event', 'Importance', 
                                   'Previous', 'Forecast', 'Actual', 'Comment'])
                    
                    # Write events
                    for event in sorted(self.filtered_events, key=lambda x: x.date_time):
                        writer.writerow([
                            event.date_time.strftime('%Y-%m-%d'),
                            event.date_time.strftime('%H:%M'),
                            event.currency,
                            event.event,
                            event.importance,
                            event.previous,
                            event.forecast,
                            event.actual,
                            event.comment
                        ])
                
                messagebox.showinfo("Success", f"Calendar exported to:\n{file_path}")
                logger.info(f"Economic calendar exported to: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export calendar:\n{str(e)}")
                logger.error(f"Error exporting calendar: {e}")
    
    def add_event_dialog(self):
        """Show dialog to add new economic event"""
        dialog = AddEventDialog(self.frame, self.add_event_callback)
    
    def add_event_callback(self, event_data: Dict[str, Any]):
        """Callback to add new event"""
        try:
            event = NewsEvent(
                date_time=event_data['date_time'],
                currency=event_data['currency'],
                event=event_data['event'],
                importance=event_data['importance'],
                previous=event_data.get('previous', ''),
                forecast=event_data.get('forecast', ''),
                actual=event_data.get('actual', ''),
                comment=event_data.get('comment', '')
            )
            
            self.news_events.append(event)
            self.apply_filters()
            self.status_label.config(text="Event added", foreground="green")
            logger.info(f"Added new event: {event.event}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add event:\n{str(e)}")
            logger.error(f"Error adding event: {e}")
    
    def remove_selected_event(self):
        """Remove the selected event"""
        selection = self.calendar_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to remove")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to remove the selected event?"):
            try:
                # Get selected event index
                item = selection[0]
                index = self.calendar_tree.index(item)
                
                if 0 <= index < len(self.filtered_events):
                    event_to_remove = self.filtered_events[index]
                    
                    # Remove from main list
                    if event_to_remove in self.news_events:
                        self.news_events.remove(event_to_remove)
                    
                    self.apply_filters()
                    self.status_label.config(text="Event removed", foreground="green")
                    logger.info(f"Removed event: {event_to_remove.event}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove event:\n{str(e)}")
                logger.error(f"Error removing event: {e}")
    
    def edit_selected_event(self):
        """Edit the selected event"""
        selection = self.calendar_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to edit")
            return
        
        try:
            item = selection[0]
            index = self.calendar_tree.index(item)
            
            if 0 <= index < len(self.filtered_events):
                event = self.filtered_events[index]
                dialog = EditEventDialog(self.frame, event, self.edit_event_callback)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit event:\n{str(e)}")
            logger.error(f"Error editing event: {e}")
    
    def edit_event_callback(self, original_event: NewsEvent, new_data: Dict[str, Any]):
        """Callback to update edited event"""
        try:
            # Find and update the original event
            if original_event in self.news_events:
                idx = self.news_events.index(original_event)
                
                # Update event data
                self.news_events[idx].date_time = new_data['date_time']
                self.news_events[idx].currency = new_data['currency']
                self.news_events[idx].event = new_data['event']
                self.news_events[idx].importance = new_data['importance']
                self.news_events[idx].previous = new_data.get('previous', '')
                self.news_events[idx].forecast = new_data.get('forecast', '')
                self.news_events[idx].actual = new_data.get('actual', '')
                self.news_events[idx].comment = new_data.get('comment', '')
                
                self.apply_filters()
                self.status_label.config(text="Event updated", foreground="green")
                logger.info(f"Updated event: {new_data['event']}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update event:\n{str(e)}")
            logger.error(f"Error updating event: {e}")
    
    def copy_event_details(self):
        """Copy selected event details to clipboard"""
        selection = self.calendar_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to copy")
            return
        
        try:
            item = selection[0]
            index = self.calendar_tree.index(item)
            
            if 0 <= index < len(self.filtered_events):
                event = self.filtered_events[index]
                
                details = f"Event: {event.event}\n"
                details += f"Date/Time: {event.date_time.strftime('%Y-%m-%d %H:%M')}\n"
                details += f"Currency: {event.currency}\n"
                details += f"Importance: {event.importance}\n"
                details += f"Previous: {event.previous}\n"
                details += f"Forecast: {event.forecast}\n"
                details += f"Actual: {event.actual}\n"
                if event.comment:
                    details += f"Comment: {event.comment}\n"
                
                self.frame.clipboard_clear()
                self.frame.clipboard_append(details)
                self.status_label.config(text="Event details copied", foreground="green")
        
        except Exception as e:
            logger.error(f"Error copying event details: {e}")
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except tk.TclError as e:
            logger.debug(f"Failed to show context menu: {e}")
    
    def on_event_double_click(self, event):
        """Handle double-click on event"""
        self.edit_selected_event()
    
    def refresh_data(self):
        """Force refresh of calendar data"""
        logger.info("Refreshing economic calendar data")
        self.reload_calendar()

class AddEventDialog:
    """Dialog for adding new economic events"""
    
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.dialog = None
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the add event dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add Economic Event")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.transient(self.parent)
        
        # Form fields
        fields_frame = ttk.Frame(self.dialog, padding=20)
        fields_frame.pack(fill=tk.BOTH, expand=True)
        
        # Date and Time
        ttk.Label(fields_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(fields_frame, textvariable=self.date_var, width=25)
        date_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        ttk.Label(fields_frame, text="Time (HH:MM):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.time_var = tk.StringVar(value="12:00")
        time_entry = ttk.Entry(fields_frame, textvariable=self.time_var, width=25)
        time_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Currency
        ttk.Label(fields_frame, text="Currency:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(fields_frame, textvariable=self.currency_var,
                                     values=["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"],
                                     width=22)
        currency_combo.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Event name
        ttk.Label(fields_frame, text="Event:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.event_var = tk.StringVar()
        event_entry = ttk.Entry(fields_frame, textvariable=self.event_var, width=25)
        event_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Importance
        ttk.Label(fields_frame, text="Importance:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.importance_var = tk.StringVar(value="Medium")
        importance_combo = ttk.Combobox(fields_frame, textvariable=self.importance_var,
                                       values=["Low", "Medium", "High"], state="readonly", width=22)
        importance_combo.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Previous
        ttk.Label(fields_frame, text="Previous:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.previous_var = tk.StringVar()
        previous_entry = ttk.Entry(fields_frame, textvariable=self.previous_var, width=25)
        previous_entry.grid(row=5, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Forecast
        ttk.Label(fields_frame, text="Forecast:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.forecast_var = tk.StringVar()
        forecast_entry = ttk.Entry(fields_frame, textvariable=self.forecast_var, width=25)
        forecast_entry.grid(row=6, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Actual
        ttk.Label(fields_frame, text="Actual:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.actual_var = tk.StringVar()
        actual_entry = ttk.Entry(fields_frame, textvariable=self.actual_var, width=25)
        actual_entry.grid(row=7, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Comment
        ttk.Label(fields_frame, text="Comment:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.comment_text = tk.Text(fields_frame, height=3, width=25)
        self.comment_text.grid(row=8, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=20)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Add Event", command=self.add_event).pack(side=tk.RIGHT)
    
    def add_event(self):
        """Add the new event"""
        try:
            # Validate and parse input
            date_str = f"{self.date_var.get()} {self.time_var.get()}"
            event_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            
            if not self.event_var.get().strip():
                messagebox.showerror("Error", "Event name is required")
                return
            
            event_data = {
                'date_time': event_datetime,
                'currency': self.currency_var.get(),
                'event': self.event_var.get().strip(),
                'importance': self.importance_var.get(),
                'previous': self.previous_var.get(),
                'forecast': self.forecast_var.get(),
                'actual': self.actual_var.get(),
                'comment': self.comment_text.get(1.0, tk.END).strip()
            }
            
            self.callback(event_data)
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date/time format. Use YYYY-MM-DD and HH:MM")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add event:\n{str(e)}")

class EditEventDialog:
    """Dialog for editing existing economic events"""
    
    def __init__(self, parent, event: NewsEvent, callback):
        self.parent = parent
        self.event = event
        self.callback = callback
        self.dialog = None
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the edit event dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Economic Event")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.transient(self.parent)
        
        # Form fields with current values
        fields_frame = ttk.Frame(self.dialog, padding=20)
        fields_frame.pack(fill=tk.BOTH, expand=True)
        
        # Date and Time
        ttk.Label(fields_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(value=self.event.date_time.strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(fields_frame, textvariable=self.date_var, width=25)
        date_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        ttk.Label(fields_frame, text="Time (HH:MM):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.time_var = tk.StringVar(value=self.event.date_time.strftime("%H:%M"))
        time_entry = ttk.Entry(fields_frame, textvariable=self.time_var, width=25)
        time_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Currency
        ttk.Label(fields_frame, text="Currency:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.currency_var = tk.StringVar(value=self.event.currency)
        currency_combo = ttk.Combobox(fields_frame, textvariable=self.currency_var,
                                     values=["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"],
                                     width=22)
        currency_combo.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Event name
        ttk.Label(fields_frame, text="Event:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.event_var = tk.StringVar(value=self.event.event)
        event_entry = ttk.Entry(fields_frame, textvariable=self.event_var, width=25)
        event_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Importance
        ttk.Label(fields_frame, text="Importance:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.importance_var = tk.StringVar(value=self.event.importance)
        importance_combo = ttk.Combobox(fields_frame, textvariable=self.importance_var,
                                       values=["Low", "Medium", "High"], state="readonly", width=22)
        importance_combo.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Previous
        ttk.Label(fields_frame, text="Previous:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.previous_var = tk.StringVar(value=self.event.previous)
        previous_entry = ttk.Entry(fields_frame, textvariable=self.previous_var, width=25)
        previous_entry.grid(row=5, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Forecast
        ttk.Label(fields_frame, text="Forecast:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.forecast_var = tk.StringVar(value=self.event.forecast)
        forecast_entry = ttk.Entry(fields_frame, textvariable=self.forecast_var, width=25)
        forecast_entry.grid(row=6, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Actual
        ttk.Label(fields_frame, text="Actual:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.actual_var = tk.StringVar(value=self.event.actual)
        actual_entry = ttk.Entry(fields_frame, textvariable=self.actual_var, width=25)
        actual_entry.grid(row=7, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Comment
        ttk.Label(fields_frame, text="Comment:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.comment_text = tk.Text(fields_frame, height=3, width=25)
        self.comment_text.insert(1.0, self.event.comment)
        self.comment_text.grid(row=8, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=20)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Update Event", command=self.update_event).pack(side=tk.RIGHT)
    
    def update_event(self):
        """Update the event with new data"""
        try:
            # Validate and parse input
            date_str = f"{self.date_var.get()} {self.time_var.get()}"
            event_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            
            if not self.event_var.get().strip():
                messagebox.showerror("Error", "Event name is required")
                return
            
            new_data = {
                'date_time': event_datetime,
                'currency': self.currency_var.get(),
                'event': self.event_var.get().strip(),
                'importance': self.importance_var.get(),
                'previous': self.previous_var.get(),
                'forecast': self.forecast_var.get(),
                'actual': self.actual_var.get(),
                'comment': self.comment_text.get(1.0, tk.END).strip()
            }
            
            self.callback(self.event, new_data)
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date/time format. Use YYYY-MM-DD and HH:MM")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update event:\n{str(e)}")