try:
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QLabel,
        QDockWidget,
        QWidget,
        QVBoxLayout,
        QTabWidget,
    )
except Exception:
    QApplication = None
    QMainWindow = object

STRENGTH_INDICATORS = ["RSI", "Stochastic", "Z-Score"]


def _build_workspace_tab() -> QWidget:
    """Create the default workspace tab."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addWidget(QLabel("Central workspace — YAML editor would live here."))
    return tab


def _build_strength_tab() -> QWidget:
    """Create a tab displaying currency strength indicators."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.addWidget(QLabel("Currency strength indicators"))
    for name in STRENGTH_INDICATORS:
        layout.addWidget(QLabel(name))
    return tab


def create_central_widget() -> QTabWidget:
    """Construct the central tab widget for the main window."""
    tabs = QTabWidget()
    tabs.addTab(_build_workspace_tab(), "Workspace")
    tabs.addTab(_build_strength_tab(), "Strength")
    return tabs


def launch_ui():
    if QApplication is None:
        print("PySide6 is not installed. Install PySide6 to run the desktop app.")
        return
    app = QApplication([])
    win = QMainWindow()
    win.setWindowTitle("APF Desktop (stub)")

    # Central widget with tabs
    win.setCentralWidget(create_central_widget())

    # Problems dock
    dock = QDockWidget("Problems")
    dock.setWidget(QLabel("Diagnostics panel (stub)"))
    win.addDockWidget(0x1, dock)  # Left dock area

    win.resize(900, 600)
    win.show()
    app.exec()
