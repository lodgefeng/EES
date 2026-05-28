# -*- coding: utf-8 -*-
"""AI experiment placement judgement page.

This module is intentionally self-contained so it can be copied into the real
AR_Camera_Ollama ``app`` package before the home page is wired to it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "AR_Camera_Ollama"
CALIBRATION_FILE = "ai_experiment_judgement_calibration.json"
REFERENCE_FILE = "ai_experiment_reference.jpg"


@dataclass
class OverlayCalibration:
    scale_percent: int = 100
    offset_x: int = 0
    offset_y: int = 0
    threshold: int = 75
    camera_index: int = 0


class AIExperimentJudgementWidget(QWidget):
    """Camera + reference-image judgement UI for fixed optical experiments."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI实验判断")

        self.calibration = OverlayCalibration()
        self.camera: Optional[cv2.VideoCapture] = None
        self.current_frame: Optional[np.ndarray] = None
        self.reference_image: Optional[np.ndarray] = None
        self.reference_path: Optional[Path] = None

        self.config_dir = self._default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_path = self.config_dir / CALIBRATION_FILE
        self.default_reference_path = self.config_dir / REFERENCE_FILE

        self._build_ui()
        self._load_calibration()
        self._load_default_reference()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_camera_frame)

    def _build_ui(self) -> None:
        self.video_label = QLabel("摄像头未启动")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(900, 560)
        self.video_label.setStyleSheet("background: #101820; color: #dbeafe;")

        self.result_label = QLabel("请加载标准图或拍摄标准图，然后点击“拍照判断”。")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            "font-size: 18px; padding: 10px; border: 1px solid #94a3b8;"
        )

        self.camera_index = QSpinBox()
        self.camera_index.setRange(0, 10)
        self.camera_index.valueChanged.connect(self._camera_index_changed)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 100)
        self.threshold_spin.setSuffix("%")
        self.threshold_spin.valueChanged.connect(self._threshold_changed)

        start_button = QPushButton("启动摄像头")
        start_button.clicked.connect(self.start_camera)

        stop_button = QPushButton("停止摄像头")
        stop_button.clicked.connect(self.stop_camera)

        load_reference_button = QPushButton("加载标准图")
        load_reference_button.clicked.connect(self.load_reference_image)

        capture_reference_button = QPushButton("拍摄为标准图")
        capture_reference_button.clicked.connect(self.capture_reference_image)

        judge_button = QPushButton("拍照判断")
        judge_button.clicked.connect(self.judge_current_frame)
        judge_button.setStyleSheet("font-size: 18px; font-weight: bold;")

        save_button = QPushButton("保存校准")
        save_button.clicked.connect(self.save_calibration)

        zoom_in_button = QPushButton("+ 放大")
        zoom_in_button.clicked.connect(lambda: self.adjust_scale(5))

        zoom_out_button = QPushButton("- 缩小")
        zoom_out_button.clicked.connect(lambda: self.adjust_scale(-5))

        up_button = QPushButton("↑")
        up_button.clicked.connect(lambda: self.adjust_offset(0, -5))

        down_button = QPushButton("↓")
        down_button.clicked.connect(lambda: self.adjust_offset(0, 5))

        left_button = QPushButton("←")
        left_button.clicked.connect(lambda: self.adjust_offset(-5, 0))

        right_button = QPushButton("→")
        right_button.clicked.connect(lambda: self.adjust_offset(5, 0))

        reset_button = QPushButton("重置叠图")
        reset_button.clicked.connect(self.reset_overlay)

        top_controls = QHBoxLayout()
        top_controls.addWidget(QLabel("摄像头:"))
        top_controls.addWidget(self.camera_index)
        top_controls.addWidget(QLabel("通过阈值:"))
        top_controls.addWidget(self.threshold_spin)
        top_controls.addWidget(start_button)
        top_controls.addWidget(stop_button)
        top_controls.addWidget(load_reference_button)
        top_controls.addWidget(capture_reference_button)
        top_controls.addWidget(judge_button)

        overlay_group = QGroupBox("AR叠图校准")
        overlay_layout = QGridLayout(overlay_group)
        overlay_layout.addWidget(zoom_in_button, 0, 0)
        overlay_layout.addWidget(zoom_out_button, 0, 1)
        overlay_layout.addWidget(up_button, 0, 3)
        overlay_layout.addWidget(left_button, 1, 2)
        overlay_layout.addWidget(right_button, 1, 4)
        overlay_layout.addWidget(down_button, 2, 3)
        overlay_layout.addWidget(reset_button, 2, 0)
        overlay_layout.addWidget(save_button, 2, 1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_controls)
        layout.addWidget(self.video_label)
        layout.addWidget(overlay_group)
        layout.addWidget(self.result_label)

    def _default_config_dir(self) -> Path:
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Creolight" / APP_NAME
        return Path.home() / f".{APP_NAME.lower()}"

    def _load_calibration(self) -> None:
        if not self.calibration_path.exists():
            self._sync_controls()
            return
        try:
            data = json.loads(self.calibration_path.read_text(encoding="utf-8"))
            self.calibration = OverlayCalibration(**data)
        except Exception as exc:  # noqa: BLE001 - keep UI resilient
            self.result_label.setText(f"读取校准失败，将使用默认值：{exc}")
        self._sync_controls()

    def _sync_controls(self) -> None:
        self.camera_index.blockSignals(True)
        self.threshold_spin.blockSignals(True)
        self.camera_index.setValue(self.calibration.camera_index)
        self.threshold_spin.setValue(self.calibration.threshold)
        self.camera_index.blockSignals(False)
        self.threshold_spin.blockSignals(False)

    def _load_default_reference(self) -> None:
        if self.default_reference_path.exists():
            self._set_reference(self.default_reference_path)

    def start_camera(self) -> None:
        self.stop_camera()
        self.camera = cv2.VideoCapture(self.calibration.camera_index, cv2.CAP_DSHOW)
        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(self.calibration.camera_index)
        if not self.camera.isOpened():
            self.camera = None
            self.result_label.setText("摄像头启动失败，请检查摄像头编号或设备连接。")
            return
        self.timer.start(30)
        self.result_label.setText("摄像头已启动。")

    def stop_camera(self) -> None:
        self.timer.stop()
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def _read_camera_frame(self) -> None:
        if self.camera is None:
            return
        ok, frame = self.camera.read()
        if not ok:
            return
        self.current_frame = frame
        self._show_frame(frame)

    def _show_frame(self, frame: np.ndarray) -> None:
        display = self._compose_overlay(frame)
        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)

    def _compose_overlay(self, frame: np.ndarray) -> np.ndarray:
        if self.reference_image is None:
            return frame.copy()
        canvas = frame.copy()
        transformed, mask = self._reference_canvas(frame.shape[:2])
        if transformed is None or mask is None:
            return canvas
        alpha = 0.42
        overlay_area = mask > 0
        canvas[overlay_area] = cv2.addWeighted(
            canvas[overlay_area],
            1.0 - alpha,
            transformed[overlay_area],
            alpha,
            0,
        )
        return canvas

    def _reference_canvas(
        self, frame_hw: Tuple[int, int]
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if self.reference_image is None:
            return None, None
        frame_h, frame_w = frame_hw
        ref_h, ref_w = self.reference_image.shape[:2]
        scale = max(1, self.calibration.scale_percent) / 100.0
        new_w = max(1, int(ref_w * scale))
        new_h = max(1, int(ref_h * scale))
        resized = cv2.resize(self.reference_image, (new_w, new_h))

        x = int((frame_w - new_w) / 2 + self.calibration.offset_x)
        y = int((frame_h - new_h) / 2 + self.calibration.offset_y)

        canvas = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
        mask = np.zeros((frame_h, frame_w), dtype=np.uint8)

        dst_x1 = max(0, x)
        dst_y1 = max(0, y)
        dst_x2 = min(frame_w, x + new_w)
        dst_y2 = min(frame_h, y + new_h)
        if dst_x1 >= dst_x2 or dst_y1 >= dst_y2:
            return canvas, mask

        src_x1 = dst_x1 - x
        src_y1 = dst_y1 - y
        src_x2 = src_x1 + (dst_x2 - dst_x1)
        src_y2 = src_y1 + (dst_y2 - dst_y1)

        roi = resized[src_y1:src_y2, src_x1:src_x2]
        canvas[dst_y1:dst_y2, dst_x1:dst_x2] = roi
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mask[dst_y1:dst_y2, dst_x1:dst_x2] = (gray > 8).astype(np.uint8) * 255
        return canvas, mask

    def load_reference_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择标准摆放图片",
            str(self.config_dir),
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if filename:
            self._set_reference(Path(filename), copy_to_default=True)

    def capture_reference_image(self) -> None:
        if self.current_frame is None:
            self.result_label.setText("当前没有摄像头画面，无法拍摄标准图。")
            return
        cv2.imwrite(str(self.default_reference_path), self.current_frame)
        self._set_reference(self.default_reference_path)
        self.result_label.setText(f"已保存标准图：{self.default_reference_path}")

    def _set_reference(self, path: Path, copy_to_default: bool = False) -> None:
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            self.result_label.setText(f"标准图读取失败：{path}")
            return
        self.reference_image = image
        self.reference_path = path
        if copy_to_default and path != self.default_reference_path:
            cv2.imwrite(str(self.default_reference_path), image)
            self.reference_path = self.default_reference_path
        if self.current_frame is not None:
            self._show_frame(self.current_frame)
        self.result_label.setText(f"已加载标准图：{self.reference_path}")

    def judge_current_frame(self) -> None:
        if self.current_frame is None:
            self.result_label.setText("当前没有摄像头画面，请先启动摄像头。")
            return
        if self.reference_image is None:
            self.result_label.setText("没有标准图，请先加载或拍摄标准图。")
            return

        ref_canvas, mask = self._reference_canvas(self.current_frame.shape[:2])
        if ref_canvas is None or mask is None or np.count_nonzero(mask) < 1000:
            self.result_label.setText("标准图没有和摄像头画面对齐，请调整缩放或位置。")
            return

        score = self._similarity_score(self.current_frame, ref_canvas, mask)
        passed = score >= self.calibration.threshold
        status = "摆放正确" if passed else "摆放可能不正确"
        color = "#16a34a" if passed else "#dc2626"
        self.result_label.setStyleSheet(
            f"font-size: 20px; padding: 10px; border: 2px solid {color}; color: {color};"
        )
        self.result_label.setText(
            f"{status}\n"
            f"相似度：{score:.1f}% / 阈值：{self.calibration.threshold}%\n"
            "提示：固定摄像头和器材位置后，先用标准光路保存参考图，再判断学生摆放。"
        )

    def _similarity_score(
        self, frame: np.ndarray, reference_canvas: np.ndarray, mask: np.ndarray
    ) -> float:
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ref_gray = cv2.cvtColor(reference_canvas, cv2.COLOR_BGR2GRAY)
        valid = mask > 0
        diff = cv2.absdiff(frame_gray, ref_gray)
        pixel_score = 100.0 * (1.0 - float(np.mean(diff[valid])) / 255.0)

        # A small edge term makes the score less sensitive to illumination.
        frame_edge = cv2.Canny(frame_gray, 80, 160)
        ref_edge = cv2.Canny(ref_gray, 80, 160)
        edge_diff = cv2.absdiff(frame_edge, ref_edge)
        edge_score = 100.0 * (1.0 - float(np.mean(edge_diff[valid])) / 255.0)
        return max(0.0, min(100.0, pixel_score * 0.7 + edge_score * 0.3))

    def adjust_scale(self, delta: int) -> None:
        self.calibration.scale_percent = max(
            10, min(300, self.calibration.scale_percent + delta)
        )
        if self.current_frame is not None:
            self._show_frame(self.current_frame)

    def adjust_offset(self, dx: int, dy: int) -> None:
        self.calibration.offset_x += dx
        self.calibration.offset_y += dy
        if self.current_frame is not None:
            self._show_frame(self.current_frame)

    def reset_overlay(self) -> None:
        self.calibration.scale_percent = 100
        self.calibration.offset_x = 0
        self.calibration.offset_y = 0
        if self.current_frame is not None:
            self._show_frame(self.current_frame)

    def save_calibration(self) -> None:
        self.calibration_path.write_text(
            json.dumps(asdict(self.calibration), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.result_label.setText(f"校准已保存：{self.calibration_path}")

    def _camera_index_changed(self, value: int) -> None:
        self.calibration.camera_index = value

    def _threshold_changed(self, value: int) -> None:
        self.calibration.threshold = value

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        self.stop_camera()
        self.save_calibration()
        super().closeEvent(event)


class AIExperimentJudgementWindow(AIExperimentJudgementWidget):
    """Top-level window alias for simple integration from existing menus."""


def main() -> int:
    app = QApplication.instance() or QApplication([])
    window = AIExperimentJudgementWindow()
    window.resize(1120, 820)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
