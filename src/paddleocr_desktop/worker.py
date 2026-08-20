from __future__ import annotations

import os
import logging
import traceback

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from .core import normalize_result, prepare_image, sort_reading_order
from .diagnostics import diagnostic_report


logger = logging.getLogger(__name__)


class OCRWorker(QObject):
    finished = pyqtSignal(list, dict)
    failed = pyqtSignal(str, str)
    status = pyqtSignal(str)

    def __init__(self, image_path: str, max_side: int = 3800) -> None:
        super().__init__()
        self.image_path = image_path
        self.max_side = max_side

    @pyqtSlot()
    def run(self) -> None:
        prepared = None
        try:
            self.status.emit("正在优化输入图片…")
            prepared = prepare_image(self.image_path, self.max_side)
            if prepared.scale < 1:
                self.status.emit(
                    f"图片已按比例缩放：{prepared.original_size[0]}×{prepared.original_size[1]} → "
                    f"{prepared.inference_size[0]}×{prepared.inference_size[1]}"
                )
            else:
                self.status.emit("正在加载 OCR 模型；首次运行需要下载模型…")

            # BOS is more reliable than Hugging Face on many mainland networks.
            os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "BOS")
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(
                lang="ch",
                ocr_version="PP-OCRv5",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                engine="onnxruntime",
                device="cpu",
            )
            self.status.emit("正在识别文字…")
            raw = ocr.predict(str(prepared.inference_path))
            lines = sort_reading_order(normalize_result(raw, prepared.scale))
            meta = {
                "original_size": prepared.original_size,
                "inference_size": prepared.inference_size,
                "scale": prepared.scale,
            }
            self.finished.emit(lines, meta)
        except Exception as exc:  # show the complete cause chain, not PaddleX's wrapper only
            traceback_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            logger.error("OCR pipeline failed\n%s", traceback_text)
            self.failed.emit(format_exception_chain(exc), diagnostic_report(traceback_text))
        finally:
            if prepared is not None:
                prepared.cleanup()


def format_exception_chain(exc: BaseException) -> str:
    messages: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        message = "".join(traceback.format_exception_only(type(current), current)).strip()
        if message not in messages:
            messages.append(message)
        current = current.__cause__ or current.__context__
    return "\n\n根因：\n".join(messages)
