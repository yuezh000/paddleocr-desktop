from __future__ import annotations

import os
import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "BOS")
    app = QApplication(sys.argv)
    app.setApplicationName("PaddleOCR 病历识别")
    app.setOrganizationName("AtomNLP")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
