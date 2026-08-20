from __future__ import annotations

import os
import sys

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QApplication

from .diagnostics import configure_logging
from .main_window import MainWindow
from .theme import APP_STYLESHEET


def main() -> int:
    os.environ["PADDLE_PDX_MODEL_SOURCE"] = "bos"
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    app = QApplication(sys.argv)
    app.setApplicationName("PaddleOCR Desktop")
    app.setOrganizationName("AtomNLP")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    configure_logging(os.path.join(app_data, "logs"))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
