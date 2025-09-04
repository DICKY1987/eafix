"""
PySide6 desktop GUI application main entry point.
"""
from PySide6.QtWidgets import QApplication, QMainWindow
import sys

def main():
    """Main entry point for the desktop GUI application."""
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Atomic Process Framework Desktop")
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
