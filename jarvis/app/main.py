"""Application entry point: `python -m jarvis.app.main`.

Wires together config -> database -> settings -> Qt application -> main window.
Fails gracefully and prints a helpful message if the GUI cannot start (e.g. no
display available), so the import-only parts remain testable on headless CI.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def _load_stylesheet() -> str:
    qss = Path(__file__).resolve().parent.parent / "ui" / "styles.qss"
    try:
        return qss.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    from .config import get_config
    from .settings import Settings
    from ..storage.database import Database

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    env = get_config()
    db = Database()
    settings = Settings.load(db, env)

    # Log the running interpreter early - the most common voice problem is
    # JARVIS running under a different Python than the venv where the user
    # installed sounddevice/numpy.
    logging.getLogger("jarvis").info("Starting JARVIS with interpreter: %s", sys.executable)

    try:
        from PySide6.QtWidgets import QApplication
        from ..ui.main_window import MainWindow
    except ImportError as exc:  # pragma: no cover - depends on environment
        print(
            "PySide6 is required to launch the GUI. Install dependencies with:\n"
            "    pip install -r requirements.txt\n"
            f"(import error: {exc})"
        )
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setStyleSheet(_load_stylesheet())

    try:
        window = MainWindow(db, settings)
    except Exception as exc:  # pragma: no cover - environment-specific
        print(f"Could not create the main window: {exc}")
        return 1

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
