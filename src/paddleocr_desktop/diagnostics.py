from __future__ import annotations

import importlib.metadata
import logging
from logging.handlers import RotatingFileHandler
import platform
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile


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
    package_names = ("paddleocr", "paddlex", "onnxruntime", "PySide6", "numpy", "Pillow")
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


def diagnostic_snapshot(max_characters: int = 200_000) -> str:
    """Return runtime details and the latest persistent log text."""
    path = str(_LOG_PATH) if _LOG_PATH else "not configured"
    sections = [environment_summary(), f"log_file={path}"]
    if _LOG_PATH and _LOG_PATH.exists():
        for handler in logging.getLogger().handlers:
            handler.flush()
        text = _LOG_PATH.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_characters:
            text = "[earlier log content omitted]\n" + text[-max_characters:]
        sections.append(text or "[log file is empty]")
    else:
        sections.append("[log file is unavailable]")
    return "\n\n".join(sections)


def export_log_bundle(destination: str | Path) -> Path:
    output = Path(destination)
    if output.suffix.lower() != ".zip":
        output = output.with_suffix(".zip")
    with tempfile.TemporaryDirectory(prefix="paddleocr-logs-") as temporary:
        stage = Path(temporary)
        (stage / "system-info.txt").write_text(environment_summary() + "\n", encoding="utf-8")
        if _LOG_PATH:
            for candidate in _LOG_PATH.parent.glob(f"{_LOG_PATH.name}*"):
                if candidate.is_file():
                    shutil.copy2(candidate, stage / candidate.name)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for candidate in sorted(stage.iterdir()):
                archive.write(candidate, candidate.name)
    return output
