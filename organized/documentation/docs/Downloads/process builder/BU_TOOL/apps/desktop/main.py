try:
    from PySide6.QtWidgets import QApplication
except Exception:
    QApplication = None

def main():
    if QApplication is None:
        print("PySide6 is not installed. Install PySide6 to run the desktop app.")
        return
    from .ui_shell import launch_ui
    launch_ui()

if __name__ == "__main__":
    main()