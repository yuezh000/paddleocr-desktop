from __future__ import annotations

import json
import math
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageOps


SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


@dataclass(slots=True)
class OCRLine:
    text: str
    score: float
    polygon: list[list[float]]


@dataclass(slots=True)
class PreparedImage:
    source_path: Path
    inference_path: Path
    original_size: tuple[int, int]
    inference_size: tuple[int, int]
    scale: float
    temporary: bool

    def cleanup(self) -> None:
        if self.temporary:
            self.inference_path.unlink(missing_ok=True)


def prepare_image(path: str | Path, max_side: int = 3800) -> PreparedImage:
    """Apply EXIF orientation and keep the longest inference side below Paddle's limit."""
    source = Path(path).expanduser().resolve()
    if max_side < 512 or max_side > 4000:
        raise ValueError("max_side 必须在 512 到 4000 之间")

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image.load()
        original_size = image.size
        longest = max(original_size)
        scale = min(1.0, max_side / longest)
        new_size = tuple(max(1, round(value * scale)) for value in original_size)

        # Always create a normalized PNG. This makes EXIF orientation and uncommon
        # source formats behave identically in Qt and PaddleOCR.
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        if new_size != original_size:
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        handle = tempfile.NamedTemporaryFile(prefix="paddleocr-", suffix=".png", delete=False)
        handle.close()
        output = Path(handle.name)
        image.save(output, "PNG", optimize=False)

    return PreparedImage(source, output, original_size, new_size, scale, True)


def _plain_result(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    candidate = getattr(value, "json", None)
    if callable(candidate):
        candidate = candidate()
    if isinstance(candidate, str):
        return json.loads(candidate)
    if isinstance(candidate, dict):
        return candidate
    candidate = getattr(value, "res", None)
    if isinstance(candidate, dict):
        return candidate
    try:
        converted = dict(value)
    except (TypeError, ValueError):
        return {}
    return converted


def normalize_result(results: Iterable[Any], coordinate_scale: float = 1.0) -> list[OCRLine]:
    """Normalize PaddleOCR 3.x pipeline results and map boxes to original pixels."""
    lines: list[OCRLine] = []
    inverse = 1.0 / coordinate_scale if coordinate_scale else 1.0
    for page in results:
        data = _plain_result(page)
        data = data.get("res", data)
        texts = data.get("rec_texts") or data.get("texts") or []
        scores = data.get("rec_scores") or data.get("scores") or []
        polygons = data.get("rec_polys") or data.get("dt_polys") or data.get("polys") or []
        for index, text in enumerate(texts):
            score = float(scores[index]) if index < len(scores) else 0.0
            raw_poly = polygons[index] if index < len(polygons) else []
            poly = [[float(point[0]) * inverse, float(point[1]) * inverse] for point in raw_poly]
            lines.append(OCRLine(str(text), score, poly))
    return lines


def lines_to_json(lines: list[OCRLine]) -> str:
    return json.dumps([asdict(line) for line in lines], ensure_ascii=False, indent=2)


def sort_reading_order(lines: list[OCRLine]) -> list[OCRLine]:
    def key(line: OCRLine) -> tuple[float, float]:
        if not line.polygon:
            return math.inf, math.inf
        return min(p[1] for p in line.polygon), min(p[0] for p in line.polygon)
    return sorted(lines, key=key)
