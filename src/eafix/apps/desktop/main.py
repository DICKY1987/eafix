"""Entry point for the desktop UI.

When the desktop GUI is launched we also want to spawn a MetaTrader 4
terminal so the two applications are available side by side.  The MT4
executable location can be supplied via the ``MT4_PATH`` environment
variable.  If it is not provided we try a couple of common install
locations on Windows.  Failing that, a warning is printed but the GUI
still launches.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

try:  # PySide6 is optional for environments running the tests
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover - handled gracefully at runtime
    QApplication = None

logger = logging.getLogger(__name__)


def launch_mt4() -> None:
    """Best-effort launch of the MetaTrader 4 terminal.

    The function first checks the ``MT4_PATH`` environment variable. If it is
    not set, typical installation paths on Windows are probed. If an executable
    cannot be found the user is informed but no exception is raised.
    """

    candidates: list[Path] = []

    env_path = os.environ.get("MT4_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())

    if os.name == "nt":  # only probe standard install locations on Windows
        candidates.extend(
            [
                Path(r"C:/Program Files/MetaTrader 4/terminal.exe"),
                Path(r"C:/Program Files (x86)/MetaTrader 4/terminal.exe"),
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            try:
                subprocess.Popen([str(candidate)])
            except OSError as exc:  # pragma: no cover - depends on OS
                logger.warning("Failed to launch MT4 at %s: %s", candidate, exc)
            return

    logger.warning(
        "MT4 executable not found. Set the MT4_PATH environment variable to the path of terminal.exe."
    )


def main() -> None:
    if QApplication is None:
        logger.error("PySide6 is not installed. Install PySide6 to run the desktop app.")
        return
    launch_mt4()
    from .ui_shell import launch_ui

    launch_ui()


if __name__ == "__main__":
    main()
