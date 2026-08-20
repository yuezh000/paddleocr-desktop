from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QPointF, Qt, QThread, QTimer
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QDragEnterEvent, QDropEvent, QImageReader, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsPixmapItem, QGraphicsPolygonItem,
    QGraphicsScene, QGraphicsView, QHeaderView, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QProgressBar, QSplitter, QStackedLayout, QStyle, QTableWidget,
    QTableWidgetItem, QToolBar, QVBoxLayout, QWidget,
)

from .core import OCRLine, SUPPORTED_IMAGES, lines_to_json
from .diagnostics import diagnostic_snapshot, export_log_bundle, log_path
from .worker import OCRWorker


class ImageView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("imageCanvas")
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._boxes: list[QGraphicsPolygonItem] = []

    def load(self, path: str) -> bool:
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            return False
        from PyQt6.QtGui import QPixmap
        self.scene().clear()
        self._boxes.clear()
        self._pixmap_item = self.scene().addPixmap(QPixmap.fromImage(image))
        self.scene().setSceneRect(self._pixmap_item.boundingRect())
        self.fit()
        return True

    def set_boxes(self, lines: list[OCRLine]) -> None:
        for item in self._boxes:
            self.scene().removeItem(item)
        self._boxes.clear()
        for line in lines:
            polygon = QPolygonF([QPointF(*point) for point in line.polygon])
            item = QGraphicsPolygonItem(polygon)
            item.setPen(QPen(QColor("#17a2b8"), 3))
            item.setBrush(QColor(23, 162, 184, 28))
            item.setZValue(2)
            self.scene().addItem(item)
            self._boxes.append(item)

    def highlight(self, index: int) -> None:
        for i, item in enumerate(self._boxes):
            selected = i == index
            item.setPen(QPen(QColor("#ff6b35" if selected else "#17a2b8"), 5 if selected else 3))
            item.setBrush(QColor(255, 107, 53, 70) if selected else QColor(23, 162, 184, 28))
        if 0 <= index < len(self._boxes):
            self.centerOn(self._boxes[index])

    def fit(self) -> None:
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class LoadingSpinner(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(70)
        self._timer.timeout.connect(self._advance)

    def start(self) -> None:
        self._timer.start()
        self.show()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _advance(self) -> None:
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        radius = 23
        for index in range(12):
            color = QColor("#126ed0")
            color.setAlpha(45 + index * 17)
            painter.setPen(QPen(color, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(0, -radius, 0, -radius + 9)
            painter.rotate(30)


class LoadingOverlay(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resultLoading")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        self.spinner = LoadingSpinner()
        self.title = QLabel("正在识别…")
        self.title.setObjectName("loadingTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message = QLabel("正在准备 OCR 模型")
        self.message.setObjectName("loadingMessage")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.title)
        layout.addWidget(self.message)
        self.hide()

    def start(self) -> None:
        self.message.setText("正在准备 OCR 模型")
        self.show()
        self.raise_()
        self.spinner.start()

    def stop(self) -> None:
        self.spinner.stop()
        self.hide()

    def set_message(self, message: str) -> None:
        self.message.setText(message)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PaddleOCR Desktop")
        self.resize(1400, 860)
        self.setAcceptDrops(True)
        self.image_path: str | None = None
        self.lines: list[OCRLine] = []
        self.thread: QThread | None = None
        self.worker: OCRWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = QToolBar("工具")
        toolbar.setObjectName("actionBar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        self.open_action = QAction("打开图片", self)
        self.open_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_image)
        toolbar.addAction(self.open_action)
        self.run_action = QAction("开始识别", self)
        self.run_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.run_action.setShortcut("Ctrl+R")
        self.run_action.setEnabled(False)
        self.run_action.triggered.connect(self.recognize)
        toolbar.addAction(self.run_action)
        self.cancel_action = QAction("取消任务", self)
        self.cancel_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.cancel_action.setEnabled(False)
        self.cancel_action.triggered.connect(self.cancel_recognition)
        toolbar.addAction(self.cancel_action)
        toolbar.addSeparator()
        fit_action = QAction("适合窗口", self)
        fit_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton))
        fit_action.triggered.connect(self.image_view_fit)
        toolbar.addAction(fit_action)
        self.copy_action = QAction("复制全文", self)
        self.copy_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.copy_action.setEnabled(False)
        self.copy_action.triggered.connect(self.copy_text)
        toolbar.addAction(self.copy_action)
        self.export_txt_action = QAction("导出 TXT", self)
        self.export_txt_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.export_txt_action.setEnabled(False)
        self.export_txt_action.triggered.connect(self.export_txt)
        toolbar.addAction(self.export_txt_action)
        self.export_json_action = QAction("导出 JSON", self)
        self.export_json_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveHDIcon))
        self.export_json_action.setEnabled(False)
        self.export_json_action.triggered.connect(self.export_json)
        toolbar.addAction(self.export_json_action)

        log_menu = self.menuBar().addMenu("日志")
        copy_logs_action = QAction("复制诊断信息", self)
        copy_logs_action.setShortcut("Ctrl+Shift+C")
        copy_logs_action.triggered.connect(self.copy_diagnostic_logs)
        log_menu.addAction(copy_logs_action)
        export_logs_action = QAction("导出日志包…", self)
        export_logs_action.triggered.connect(self.export_diagnostic_logs)
        log_menu.addAction(export_logs_action)
        log_menu.addSeparator()
        open_logs_action = QAction("打开日志目录", self)
        open_logs_action.triggered.connect(self.open_log_directory)
        log_menu.addAction(open_logs_action)

        root = QWidget()
        root.setObjectName("appRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 15, 18, 15)
        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        title = QLabel("PaddleOCR Desktop")
        title.setObjectName("heroTitle")
        subtitle = QLabel("在本机完成图片文字识别，对照查看每一处结果")
        subtitle.setObjectName("heroSubtitle")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        hero_layout.addLayout(title_group)
        hero_layout.addStretch()
        badge = QLabel("PP-OCRv5  ·  本地处理")
        badge.setObjectName("engineBadge")
        hero_layout.addWidget(badge)
        root_layout.addWidget(hero)

        self.image_view = ImageView()
        left = QFrame()
        left.setProperty("class", "card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 13, 14, 14)
        left_layout.setSpacing(9)
        left_header = QHBoxLayout()
        left_title = QLabel("原始图片与检测框")
        left_title.setProperty("class", "panelTitle")
        self.image_label = QLabel("将图片拖到这里，或点击“打开图片”")
        self.image_label.setObjectName("fileLabel")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        left_header.addWidget(left_title)
        left_header.addStretch()
        left_header.addWidget(self.image_label, 1)
        left_layout.addLayout(left_header)
        left_layout.addWidget(self.image_view, 1)

        self.table = QTableWidget(0, 3)
        self.table.setObjectName("resultTable")
        self.table.setHorizontalHeaderLabels(["识别文字", "置信度", "位置"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(39)
        self.table.currentCellChanged.connect(lambda row, _c, _pr, _pc: self.image_view.highlight(row))

        right = QFrame()
        right.setProperty("class", "card")
        right_stack = QStackedLayout(right)
        right_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        right_content = QWidget()
        right_content.setObjectName("resultContent")
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(14, 13, 14, 14)
        right_layout.setSpacing(9)
        right_title = QLabel("识别结果")
        right_title.setProperty("class", "panelTitle")
        self.result_count = QLabel("尚未识别")
        self.result_count.setObjectName("fileLabel")
        right_header = QHBoxLayout()
        right_header.addWidget(right_title)
        right_header.addStretch()
        right_header.addWidget(self.result_count)
        right_layout.addLayout(right_header)
        right_layout.addWidget(self.table, 1)
        right_stack.addWidget(right_content)
        self.loading_overlay = LoadingOverlay()
        right_stack.addWidget(self.loading_overlay)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([820, 520])
        splitter.setChildrenCollapsible(False)
        root_layout.addWidget(splitter, 1)
        self.setCentralWidget(root)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(170)
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.statusBar().addPermanentWidget(self.progress)
        self.statusBar().showMessage("就绪")

    def image_view_fit(self) -> None:
        self.image_view.fit()

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"
        )
        if path:
            self.load_image(path)

    def load_image(self, path: str) -> None:
        if Path(path).suffix.lower() not in SUPPORTED_IMAGES or not self.image_view.load(path):
            QMessageBox.warning(self, "无法打开", "请选择有效的 PNG、JPEG、BMP、TIFF 或 WebP 图片。")
            return
        self.image_path = path
        self.lines = []
        self.table.setRowCount(0)
        self.result_count.setText("尚未识别")
        self.image_view.set_boxes([])
        self.image_label.setText(Path(path).name)
        self.run_action.setEnabled(True)
        self._set_result_actions(False)
        self.statusBar().showMessage("图片已打开，点击“开始识别”")

    def recognize(self) -> None:
        if not self.image_path or self.thread:
            return
        self.run_action.setEnabled(False)
        self.open_action.setEnabled(False)
        self.cancel_action.setEnabled(True)
        self.progress.show()
        self.result_count.setText("正在识别")
        self.loading_overlay.start()
        self.thread = QThread(self)
        self.worker = OCRWorker(self.image_path, max_side=3800)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.status.connect(self._recognition_status)
        self.worker.finished.connect(self._recognition_done)
        self.worker.failed.connect(self._recognition_failed)
        self.worker.cancelled.connect(self._recognition_cancelled)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.worker.cancelled.connect(self.thread.quit)
        self.thread.finished.connect(self._thread_finished)
        self.thread.start()

    def cancel_recognition(self) -> None:
        if not self.worker:
            return
        self.worker.request_cancel()
        self.cancel_action.setEnabled(False)
        self.loading_overlay.title.setText("正在取消…")
        self.loading_overlay.set_message("将在当前推理步骤结束后安全取消")
        self.statusBar().showMessage("已请求取消，正在等待当前推理步骤结束…")

    def _recognition_cancelled(self) -> None:
        self.result_count.setText("已取消")
        self.statusBar().showMessage("识别任务已取消")

    def _recognition_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
        self.loading_overlay.set_message(message)

    def _recognition_done(self, lines: list, meta: dict) -> None:
        self.lines = lines
        self.image_view.set_boxes(lines)
        self.table.setRowCount(len(lines))
        for row, line in enumerate(lines):
            self.table.setItem(row, 0, QTableWidgetItem(line.text))
            self.table.setItem(row, 1, QTableWidgetItem(f"{line.score:.1%}"))
            position = "—"
            if line.polygon:
                xs, ys = [p[0] for p in line.polygon], [p[1] for p in line.polygon]
                position = f"{min(xs):.0f},{min(ys):.0f}"
            self.table.setItem(row, 2, QTableWidgetItem(position))
        self._set_result_actions(bool(lines))
        self.result_count.setText(f"{len(lines)} 个文本区域")
        original = "×".join(map(str, meta["original_size"]))
        inference = "×".join(map(str, meta["inference_size"]))
        size_note = f"；推理尺寸 {inference}" if original != inference else ""
        self.statusBar().showMessage(f"识别完成：{len(lines)} 个文本区域{size_note}")

    def _recognition_failed(self, message: str, diagnostics: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("识别失败")
        box.setText("PaddleOCR 未能完成识别")
        box.setInformativeText(message)
        box.setDetailedText(diagnostics)
        box.setStandardButtons(QMessageBox.StandardButton.Close)
        copy_button = box.addButton("复制完整日志", QMessageBox.ButtonRole.ActionRole)
        folder_button = box.addButton("打开日志目录", QMessageBox.ButtonRole.ActionRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is copy_button:
            QApplication.clipboard().setText(diagnostics)
            self.statusBar().showMessage("完整诊断日志已复制")
        elif clicked is folder_button:
            self.open_log_directory()
        else:
            self.statusBar().showMessage("识别失败")

    def _thread_finished(self) -> None:
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None
        self.progress.hide()
        self.loading_overlay.stop()
        self.loading_overlay.title.setText("正在识别…")
        self.open_action.setEnabled(True)
        self.cancel_action.setEnabled(False)
        self.run_action.setEnabled(bool(self.image_path))

    def copy_diagnostic_logs(self) -> None:
        QApplication.clipboard().setText(diagnostic_snapshot())
        self.statusBar().showMessage("诊断信息和最新日志已复制")

    def export_diagnostic_logs(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self, "导出日志包", "paddleocr-desktop-logs.zip", "ZIP 压缩包 (*.zip)"
        )
        if not destination:
            return
        try:
            output = export_log_bundle(destination)
        except OSError as exc:
            QMessageBox.warning(self, "导出失败", f"无法导出日志：{exc}")
            return
        self.statusBar().showMessage(f"日志已导出到 {output}")

    def open_log_directory(self) -> None:
        path = log_path()
        if path:
            QDesktopServices.openUrl(path.parent.resolve().as_uri())
            self.statusBar().showMessage("已打开日志目录")
        else:
            QMessageBox.warning(self, "日志不可用", "日志目录尚未初始化。")

    def _set_result_actions(self, enabled: bool) -> None:
        self.copy_action.setEnabled(enabled)
        self.export_txt_action.setEnabled(enabled)
        self.export_json_action.setEnabled(enabled)

    def copy_text(self) -> None:
        QApplication.clipboard().setText("\n".join(line.text for line in self.lines))
        self.statusBar().showMessage("识别文字已复制")

    def export_txt(self) -> None:
        self._export("txt", "\n".join(line.text for line in self.lines))

    def export_json(self) -> None:
        self._export("json", lines_to_json(self.lines))

    def _export(self, suffix: str, content: str) -> None:
        stem = Path(self.image_path or "ocr-result").stem
        path, _ = QFileDialog.getSaveFileName(self, "导出识别结果", f"{stem}.{suffix}")
        if path:
            Path(path).write_text(content, encoding="utf-8")
            self.statusBar().showMessage(f"已导出到 {path}")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(Path(u.toLocalFile()).suffix.lower() in SUPPORTED_IMAGES for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in SUPPORTED_IMAGES:
                self.load_image(path)
                break

    def closeEvent(self, event) -> None:
        if self.thread:
            self.cancel_recognition()
            QMessageBox.information(self, "正在取消", "已请求取消任务，请等待当前推理步骤结束后再退出。")
            event.ignore()
        else:
            event.accept()
