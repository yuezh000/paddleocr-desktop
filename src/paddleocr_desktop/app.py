from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .diagnostics import configure_logging
from .main_window import MainWindow
from .resources import resource_path
from .theme import APP_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PaddleOCR Desktop")
    app.setOrganizationName("AtomNLP")
    app.setWindowIcon(QIcon(str(resource_path("assets/app-icon.svg"))))
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    configure_logging(Path(app_data) / "logs")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
