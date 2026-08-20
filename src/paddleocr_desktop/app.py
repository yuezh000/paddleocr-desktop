from __future__ import annotations

import os
from pathlib import Path
import sys

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .diagnostics import configure_logging
from .main_window import MainWindow
from .theme import APP_STYLESHEET


def resource_path(relative: str) -> str:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return str(base / relative)


def main() -> int:
    os.environ["PADDLE_PDX_MODEL_SOURCE"] = "modelscope"
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    app = QApplication(sys.argv)
    app.setApplicationName("PaddleOCR Desktop")
    app.setOrganizationName("AtomNLP")
    app.setWindowIcon(QIcon(resource_path("assets/app-icon.svg")))
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    configure_logging(os.path.join(app_data, "logs"))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
