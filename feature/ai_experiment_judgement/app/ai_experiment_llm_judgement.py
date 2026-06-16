# -*- coding: utf-8 -*-
"""Button 06: AI experiment judgement with Ollama vision model."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.experiment_shared import (
    CALIBRATION_FILE,
    CameraMixin,
    OverlayCalibration,
    REFERENCE_FILE,
    default_config_dir,
    draw_difference_circles,
    find_difference_regions,
    load_calibration,
    read_image,
    reference_canvas,
    save_calibration,
    show_frame_on_label,
    write_image,
)
from app.ollama_vision_client import guess_vision_model, judge_images_with_ollama


class OllamaJudgeWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        model: str,
        endpoint: str,
        current_b64: str,
        reference_b64: str,
        region_count: int,
    ) -> None:
        super().__init__()
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.current_b64 = current_b64
        self.reference_b64 = reference_b64
        self.region_count = region_count

    def run(self) -> None:
        try:
            text = judge_images_with_ollama(
                model=self.model,
                endpoint=self.endpoint,
                current_b64=self.current_b64,
                reference_b64=self.reference_b64,
                region_count=self.region_count,
            )
            self.finished.emit(text)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class AIExperimentLLMJudgementWidget(QWidget, CameraMixin):
    """Compare live frame with reference and explain differences via Ollama."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        home_window: Optional[QWidget] = None,
    ) -> None:
        QWidget.__init__(self, parent)
        CameraMixin.__init__(self)
        self.home_window = home_window
        self.setWindowTitle("AI实验判断")

        self.calibration = OverlayCalibration()
        self.camera = None
        self.current_frame: Optional[np.ndarray] = None
        self.reference_image: Optional[np.ndarray] = None
        self.reference_path: Optional[Path] = None
        self._worker: Optional[OllamaJudgeWorker] = None
        self._last_marked_frame: Optional[np.ndarray] = None

        self.config_dir = default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_path = self.config_dir / CALIBRATION_FILE
        self.default_reference_path = self.config_dir / REFERENCE_FILE

        self._build_ui()
        self.calibration = load_calibration(self.calibration_path)
        self._sync_controls()
        self._load_default_reference()
        self._autofill_model_name()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_camera_frame)

    def _build_ui(self) -> None:
        nav_row = QHBoxLayout()
        back_button = QPushButton("返回主目录")
        back_button.clicked.connect(self._go_home)
        nav_row.addWidget(back_button)
        nav_row.addStretch(1)

        self.video_label = QLabel("摄像头未启动")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(900, 520)
        self.video_label.setStyleSheet("background:#101820;color:#dbeafe;")

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("点击“AI判断差异”后，这里显示大模型说明。")

        self.camera_index = QSpinBox()
        self.camera_index.setRange(0, 10)
        self.camera_index.valueChanged.connect(self._camera_index_changed)

        self.model_edit = QLineEdit("qwen3-vl:2b")
        self.endpoint_edit = QLineEdit("http://127.0.0.1:11434")

        start_button = QPushButton("启动摄像头")
        start_button.clicked.connect(self.start_camera_action)
        stop_button = QPushButton("停止摄像头")
        stop_button.clicked.connect(self.stop_camera_action)
        load_reference_button = QPushButton("加载标准图")
        load_reference_button.clicked.connect(self.load_reference_image)
        judge_button = QPushButton("AI判断差异")
        judge_button.clicked.connect(self.judge_with_ollama)
        judge_button.setStyleSheet("font-size:18px;font-weight:bold;")

        top_controls = QHBoxLayout()
        top_controls.addWidget(QLabel("摄像头:"))
        top_controls.addWidget(self.camera_index)
        top_controls.addWidget(QLabel("Ollama模型:"))
        top_controls.addWidget(self.model_edit)
        top_controls.addWidget(QLabel("地址:"))
        top_controls.addWidget(self.endpoint_edit)
        top_controls.addWidget(start_button)
        top_controls.addWidget(stop_button)
        top_controls.addWidget(load_reference_button)
        top_controls.addWidget(judge_button)

        layout = QVBoxLayout(self)
        layout.addLayout(nav_row)
        layout.addLayout(top_controls)
        layout.addWidget(self.video_label)
        layout.addWidget(self.result_text)

    def _autofill_model_name(self) -> None:
        endpoint = self.endpoint_edit.text().strip() or "http://127.0.0.1:11434"
        guessed = guess_vision_model(endpoint)
        if guessed and self.model_edit.text().strip() in ("", "llava"):
            self.model_edit.setText(guessed)

    def _go_home(self) -> None:
        self.hide()
        if self.home_window is not None:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()

    def _sync_controls(self) -> None:
        self.camera_index.blockSignals(True)
        self.camera_index.setValue(self.calibration.camera_index)
        self.camera_index.blockSignals(False)

    def _load_default_reference(self) -> None:
        if self.default_reference_path.exists():
            self._set_reference(self.default_reference_path)

    def start_camera_action(self) -> None:
        ok, message = self.start_camera(self.calibration.camera_index)
        if not ok:
            self.result_text.setPlainText(message)
            return
        self.timer.start(30)
        self.result_text.setPlainText("摄像头已启动。")

    def stop_camera_action(self) -> None:
        self.timer.stop()
        self.stop_camera()
        self.result_text.setPlainText("摄像头已停止。")

    def _read_camera_frame(self) -> None:
        frame = self.read_camera_frame()
        if frame is None:
            return
        if self._last_marked_frame is None:
            show_frame_on_label(self.video_label, frame)

    def load_reference_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择标准摆放图片",
            str(self.config_dir),
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if filename:
            self._set_reference(Path(filename), copy_to_default=True)

    def _set_reference(self, path: Path, copy_to_default: bool = False) -> None:
        image = read_image(path)
        if image is None:
            self.result_text.setPlainText(f"标准图读取失败：{path}")
            return
        self.reference_image = image
        self.reference_path = path
        if copy_to_default and path != self.default_reference_path:
            write_image(self.default_reference_path, image)
            self.reference_path = self.default_reference_path
        self.result_text.setPlainText(f"已加载标准图：{self.reference_path}")

    def judge_with_ollama(self) -> None:
        if self.current_frame is None:
            self.result_text.setPlainText("请先启动摄像头。")
            return
        if self.reference_image is None:
            self.result_text.setPlainText("请先加载标准图。")
            return
        if self._worker is not None and self._worker.isRunning():
            self.result_text.setPlainText("AI 正在判断，请稍候...")
            return

        ref_canvas, mask = reference_canvas(
            self.current_frame.shape[:2],
            self.reference_image,
            self.calibration,
        )
        if ref_canvas is None or mask is None or np.count_nonzero(mask) < 1000:
            self.result_text.setPlainText("标准图未对齐，请先在“05 AR成像调节”中校准。")
            return

        circles = find_difference_regions(self.current_frame, ref_canvas, mask)
        marked = draw_difference_circles(self.current_frame, circles)
        self._last_marked_frame = marked
        show_frame_on_label(self.video_label, marked)

        current_b64 = _image_to_base64(marked)
        reference_b64 = _image_to_base64(ref_canvas)
        model = self.model_edit.text().strip() or "qwen3-vl:2b"
        endpoint = self.endpoint_edit.text().strip() or "http://127.0.0.1:11434"

        self.result_text.setPlainText(
            f"正在调用 Ollama 模型 {model} 分析差异...\n"
            "qwen3-vl 一次只支持 1 张图片，程序会自动拼接左右对比图后请求。"
        )
        self._worker = OllamaJudgeWorker(
            model=model,
            endpoint=endpoint,
            current_b64=current_b64,
            reference_b64=reference_b64,
            region_count=len(circles),
        )
        self._worker.finished.connect(self._on_judge_finished)
        self._worker.failed.connect(self._on_judge_failed)
        self._worker.start()

    def _on_judge_finished(self, text: str) -> None:
        prefix = ""
        if self._last_marked_frame is not None:
            prefix = "已在实时画面上用编号圆圈标出主要疑似差异区域。\n\n"
        self.result_text.setPlainText(prefix + text)

    def _on_judge_failed(self, message: str) -> None:
        self.result_text.setPlainText(
            "Ollama 判断失败。\n"
            f"错误：{message}\n\n"
            "请确认：\n"
            "1. Ollama 已启动（地址 http://127.0.0.1:11434）\n"
            "2. 模型名称与 Ollama 中一致，例如 qwen3-vl:2b\n"
            "3. 该模型支持视觉输入（名称含 vl / llava 等）"
        )

    def _camera_index_changed(self, value: int) -> None:
        self.calibration.camera_index = value

    def closeEvent(self, event) -> None:  # noqa: N802
        self.timer.stop()
        self.stop_camera()
        save_calibration(self.calibration_path, self.calibration)
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(2000)
        super().closeEvent(event)


class AIExperimentLLMJudgementWindow(AIExperimentLLMJudgementWidget):
    """Top-level window for button 06."""


def _image_to_base64(image: np.ndarray) -> str:
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("Could not encode image for Ollama.")
    return base64.b64encode(encoded.tobytes()).decode("ascii")
