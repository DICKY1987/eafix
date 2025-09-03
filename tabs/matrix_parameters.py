"""
HUEY_P Trading Interface - Matrix Parameters Tab
Configure matrix parameter sets used by the trading system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class MatrixParametersTab:
    """UI tab for managing matrix parameter sets"""

    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app_controller = app_controller
        self.frame = None

        # Simple in-memory storage for demonstration purposes
        self.parameter_sets: Dict[str, str] = {}

        # Editor variables
        self.name_var = tk.StringVar()
        self.value_var = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        """Build the tab UI"""
        # Main frame
        self.frame = ttk.Frame(self.parent)

        # Create layout containers
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - list of parameter sets
        self.list_frame = ttk.LabelFrame(main_container, text="📚 Parameter Sets", padding=10)
        self.list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        self.setup_parameter_list()

        # Right panel - editor
        self.editor_frame = ttk.LabelFrame(main_container, text="✏️ Edit Parameter Set", padding=10)
        self.editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.setup_editor()
        self.setup_controls()

        logger.info("Matrix parameters tab UI setup complete")

    def setup_parameter_list(self):
        """Setup list of existing parameter sets"""
        list_container = ttk.Frame(self.list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_container, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_set_selected)

    def setup_editor(self):
        """Setup editor fields"""
        self.editor_frame.columnconfigure(1, weight=1)

        ttk.Label(self.editor_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.editor_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=2)

        ttk.Label(self.editor_frame, text="Value:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.editor_frame, textvariable=self.value_var).grid(row=1, column=1, sticky=tk.EW, pady=2)

    def setup_controls(self):
        """Setup control buttons"""
        btn_frame = ttk.Frame(self.editor_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="New", command=self.new_parameter_set).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_parameter_set).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_parameter_set).pack(side=tk.LEFT, padx=5)

    def new_parameter_set(self):
        """Clear editor for new parameter set"""
        self.name_var.set("")
        self.value_var.set("")
        self.listbox.selection_clear(0, tk.END)

    def save_parameter_set(self):
        """Save or update a parameter set"""
        name = self.name_var.get().strip()
        value = self.value_var.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Name is required")
            return

        self.parameter_sets[name] = value

        # Update listbox
        current_items = list(self.listbox.get(0, tk.END))
        if name not in current_items:
            self.listbox.insert(tk.END, name)
        else:
            idx = current_items.index(name)
            self.listbox.delete(idx)
            self.listbox.insert(idx, name)
            self.listbox.selection_set(idx)

        logger.info("Saved parameter set '%s'", name)

    def delete_parameter_set(self):
        """Delete selected parameter set"""
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        name = self.listbox.get(idx)
        if messagebox.askyesno("Delete", f"Delete parameter set '{name}'?"):
            self.listbox.delete(idx)
            self.parameter_sets.pop(name, None)
            self.new_parameter_set()
            logger.info("Deleted parameter set '%s'", name)

    def on_set_selected(self, event):
        """Load selected parameter set into editor"""
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        name = self.listbox.get(idx)
        self.name_var.set(name)
        self.value_var.set(self.parameter_sets.get(name, ""))
