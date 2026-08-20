from __future__ import annotations

import os
import logging
import traceback

from PySide6.QtCore import QObject, Signal, Slot

from .core import normalize_result, prepare_image, sort_reading_order
from .diagnostics import diagnostic_report


logger = logging.getLogger(__name__)


class OCRWorker(QObject):
    finished = Signal(list, dict)
    failed = Signal(str, str)
    cancelled = Signal()
    status = Signal(str)

    def __init__(self, image_path: str, max_side: int = 3800) -> None:
        super().__init__()
        self.image_path = image_path
        self.max_side = max_side
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def _stop_if_cancelled(self) -> bool:
        if self._cancel_requested:
            self.cancelled.emit()
            return True
        return False

    @Slot()
    def run(self) -> None:
        prepared = None
        try:
            self.status.emit("正在优化输入图片…")
            prepared = prepare_image(self.image_path, self.max_side)
            if self._stop_if_cancelled():
                return
            if prepared.scale < 1:
                self.status.emit(
                    f"图片已按比例缩放：{prepared.original_size[0]}×{prepared.original_size[1]} → "
                    f"{prepared.inference_size[0]}×{prepared.inference_size[1]}"
                )
            else:
                self.status.emit("正在加载 OCR 模型；首次运行需要下载模型…")

            # ONNX packages are not available from BOS. Prefer ModelScope so
            # Windows users do not get stuck on Hugging Face's large-file CDN.
            os.environ["PADDLE_PDX_MODEL_SOURCE"] = "modelscope"
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
            from paddleocr import PaddleOCR

            logger.info(
                "Loading OCR models source=modelscope detection=PP-OCRv5_mobile_det "
                "recognition=PP-OCRv5_mobile_rec engine=onnxruntime"
            )
            ocr = PaddleOCR(
                lang="ch",
                ocr_version="PP-OCRv5",
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name="PP-OCRv5_mobile_rec",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                engine="onnxruntime",
                device="cpu",
            )
            if self._stop_if_cancelled():
                return
            self.status.emit("正在识别文字…")
            raw = ocr.predict(str(prepared.inference_path))
            if self._stop_if_cancelled():
                return
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
