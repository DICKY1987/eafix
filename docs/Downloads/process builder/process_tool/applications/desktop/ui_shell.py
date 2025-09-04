"""
Main window shell for the PySide6 desktop GUI application.
"""
from PySide6.QtWidgets import QMainWindow

class MainWindowShell(QMainWindow):
    """Main window shell for the desktop application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Atomic Process Framework Desktop Shell")
