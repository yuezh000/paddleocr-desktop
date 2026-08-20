from __future__ import annotations

import importlib.metadata
import logging
from logging.handlers import RotatingFileHandler
import platform
from pathlib import Path
import sys


_LOG_PATH: Path | None = None


def configure_logging(directory: str | Path) -> Path:
    global _LOG_PATH
    log_directory = Path(directory)
    log_directory.mkdir(parents=True, exist_ok=True)
    _LOG_PATH = log_directory / "paddleocr-desktop.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(handler, RotatingFileHandler) for handler in root.handlers):
        handler = RotatingFileHandler(
            _LOG_PATH,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root.addHandler(handler)
    logging.getLogger(__name__).info("Application started\n%s", environment_summary())
    return _LOG_PATH


def log_path() -> Path | None:
    return _LOG_PATH


def environment_summary() -> str:
    package_names = ("paddleocr", "paddlex", "onnxruntime", "PyQt6", "numpy", "Pillow")
    versions: list[str] = []
    for name in package_names:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "not installed / metadata unavailable"
        versions.append(f"{name}={version}")
    return "\n".join([
        f"OS={platform.platform()}",
        f"machine={platform.machine()}",
        f"Python={sys.version.split()[0]}",
        *versions,
    ])


def diagnostic_report(traceback_text: str) -> str:
    path = str(_LOG_PATH) if _LOG_PATH else "not configured"
    return f"{environment_summary()}\nlog_file={path}\n\n{traceback_text}".strip()
