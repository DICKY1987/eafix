try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QDockWidget, QWidget, QVBoxLayout
except Exception:
    QApplication = None
    QMainWindow = object

def launch_ui():
    if QApplication is None:
        print("PySide6 is not installed. Install PySide6 to run the desktop app.")
        return
    app = QApplication([])
    win = QMainWindow()
    win.setWindowTitle("APF Desktop (stub)")

    # Central widget
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.addWidget(QLabel("Central workspace — YAML editor would live here."))
    win.setCentralWidget(central)

    # Problems dock
    dock = QDockWidget("Problems")
    dock.setWidget(QLabel("Diagnostics panel (stub)"))
    win.addDockWidget(0x1, dock)  # Left dock area

    win.resize(900, 600)
    win.show()
    app.exec()