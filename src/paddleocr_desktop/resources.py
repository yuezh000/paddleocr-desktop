from __future__ import annotations

from pathlib import Path
import sys


def resource_path(relative: str | Path) -> Path:
    """Resolve a project asset in development and inside PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / relative


def bundled_model_paths() -> tuple[Path, Path]:
    root = resource_path("assets/models")
    detection = root / "PP-OCRv5_mobile_det_onnx"
    recognition = root / "PP-OCRv5_mobile_rec_onnx"
    required = (
        detection / "inference.onnx",
        detection / "inference.yml",
        recognition / "inference.onnx",
        recognition / "inference.yml",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("内置 OCR 模型不完整：\n" + "\n".join(missing))
    return detection, recognition

