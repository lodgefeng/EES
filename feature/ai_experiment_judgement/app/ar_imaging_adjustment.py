# -*- coding: utf-8 -*-
"""Button 05: AR imaging adjustment with dual preview and 4020 cast."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
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

from app.experiment_shared import (
    CALIBRATION_FILE,
    CameraMixin,
    OverlayCalibration,
    REFERENCE_FILE,
    compose_overlay,
    default_config_dir,
    load_calibration,
    read_image,
    reference_preview_image,
    save_calibration,
    show_frame_on_label,
    write_image,
)
from app.jbd4020_cast_support import JBD4020CastDialog


class ARImagingAdjustmentWidget(QWidget, CameraMixin):
    """Camera overlay tuning page with synced reference preview."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        home_window: Optional[QWidget] = None,
    ) -> None:
        QWidget.__init__(self, parent)
        CameraMixin.__init__(self)
        self.home_window = home_window
        self.setWindowTitle("AR成像调节")

        self.calibration = OverlayCalibration()
        self.camera = None
        self.current_frame: Optional[np.ndarray] = None
        self.reference_image: Optional[np.ndarray] = None
        self.reference_path: Optional[Path] = None
        self._cast_dialog: Optional[JBD4020CastDialog] = None

        self.config_dir = default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_path = self.config_dir / CALIBRATION_FILE
        self.default_reference_path = self.config_dir / REFERENCE_FILE

        self._build_ui()
        self.calibration = load_calibration(self.calibration_path)
        self._sync_controls()
        self._load_default_reference()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._read_camera_frame)

    def _build_ui(self) -> None:
        nav_row = QHBoxLayout()
        back_button = QPushButton("返回主目录")
        back_button.clicked.connect(self._go_home)
        cast_button = QPushButton("4020投放")
        cast_button.clicked.connect(self._open_cast_dialog)
        nav_row.addWidget(back_button)
        nav_row.addWidget(cast_button)
        nav_row.addStretch(1)

        self.overlay_label = QLabel("摄像头未启动")
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setMinimumSize(520, 420)
        self.overlay_label.setStyleSheet("background:#101820;color:#dbeafe;")

        self.reference_label = QLabel("标准图预览")
        self.reference_label.setAlignment(Qt.AlignCenter)
        self.reference_label.setMinimumSize(520, 420)
        self.reference_label.setStyleSheet("background:#101820;color:#dbeafe;")

        preview_row = QHBoxLayout()
        overlay_box = QVBoxLayout()
        overlay_box.addWidget(QLabel("AR叠图预览"))
        overlay_box.addWidget(self.overlay_label)
        reference_box = QVBoxLayout()
        reference_box.addWidget(QLabel("标准图同步预览"))
        reference_box.addWidget(self.reference_label)
        preview_row.addLayout(overlay_box)
        preview_row.addLayout(reference_box)

        self.status_label = QLabel("请启动摄像头，并加载或拍摄标准图。")
        self.status_label.setWordWrap(True)

        self.camera_index = QSpinBox()
        self.camera_index.setRange(0, 10)
        self.camera_index.valueChanged.connect(self._camera_index_changed)

        start_button = QPushButton("启动摄像头")
        start_button.clicked.connect(self.start_camera_action)
        stop_button = QPushButton("停止摄像头")
        stop_button.clicked.connect(self.stop_camera_action)
        load_reference_button = QPushButton("加载标准图")
        load_reference_button.clicked.connect(self.load_reference_image)
        capture_reference_button = QPushButton("拍摄为标准图")
        capture_reference_button.clicked.connect(self.capture_reference_image)
        save_button = QPushButton("保存校准")
        save_button.clicked.connect(self.save_calibration_action)

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
        top_controls.addWidget(start_button)
        top_controls.addWidget(stop_button)
        top_controls.addWidget(load_reference_button)
        top_controls.addWidget(capture_reference_button)
        top_controls.addWidget(save_button)

        overlay_group = QGroupBox("AR叠图校准")
        overlay_layout = QGridLayout(overlay_group)
        overlay_layout.addWidget(zoom_in_button, 0, 0)
        overlay_layout.addWidget(zoom_out_button, 0, 1)
        overlay_layout.addWidget(up_button, 0, 3)
        overlay_layout.addWidget(left_button, 1, 2)
        overlay_layout.addWidget(right_button, 1, 4)
        overlay_layout.addWidget(down_button, 2, 3)
        overlay_layout.addWidget(reset_button, 2, 0)

        layout = QVBoxLayout(self)
        layout.addLayout(nav_row)
        layout.addLayout(top_controls)
        layout.addLayout(preview_row)
        layout.addWidget(overlay_group)
        layout.addWidget(self.status_label)

    def _go_home(self) -> None:
        self.hide()
        if self._cast_dialog is not None:
            self._cast_dialog.close()
        if self.home_window is not None:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()

    def _open_cast_dialog(self) -> None:
        if self._cast_dialog is None:
            self._cast_dialog = JBD4020CastDialog(self._current_reference_preview, self)
        self._cast_dialog.show()
        self._cast_dialog.raise_()
        self._cast_dialog.activateWindow()

    def _current_reference_preview(self) -> Optional[np.ndarray]:
        if self.current_frame is None:
            return None
        return reference_preview_image(
            self.current_frame.shape[:2],
            self.reference_image,
            self.calibration,
        )

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
            self.status_label.setText(message)
            return
        self.timer.start(30)
        self.status_label.setText("摄像头已启动。")

    def stop_camera_action(self) -> None:
        self.timer.stop()
        self.stop_camera()
        self.status_label.setText("摄像头已停止。")

    def _read_camera_frame(self) -> None:
        frame = self.read_camera_frame()
        if frame is None:
            return
        self._refresh_previews(frame)

    def _refresh_previews(self, frame: np.ndarray) -> None:
        overlay = compose_overlay(frame, self.reference_image, self.calibration)
        preview = reference_preview_image(frame.shape[:2], self.reference_image, self.calibration)
        show_frame_on_label(self.overlay_label, overlay)
        show_frame_on_label(self.reference_label, preview)

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
            self.status_label.setText("当前没有摄像头画面，无法拍摄标准图。")
            return
        write_image(self.default_reference_path, self.current_frame)
        self._set_reference(self.default_reference_path)
        self.status_label.setText(f"已保存标准图：{self.default_reference_path}")

    def _set_reference(self, path: Path, copy_to_default: bool = False) -> None:
        image = read_image(path)
        if image is None:
            self.status_label.setText(f"标准图读取失败：{path}")
            return
        self.reference_image = image
        self.reference_path = path
        if copy_to_default and path != self.default_reference_path:
            write_image(self.default_reference_path, image)
            self.reference_path = self.default_reference_path
        if self.current_frame is not None:
            self._refresh_previews(self.current_frame)
        self.status_label.setText(f"已加载标准图：{self.reference_path}")

    def adjust_scale(self, delta: int) -> None:
        self.calibration.scale_percent = max(10, min(300, self.calibration.scale_percent + delta))
        if self.current_frame is not None:
            self._refresh_previews(self.current_frame)

    def adjust_offset(self, dx: int, dy: int) -> None:
        self.calibration.offset_x += dx
        self.calibration.offset_y += dy
        if self.current_frame is not None:
            self._refresh_previews(self.current_frame)

    def reset_overlay(self) -> None:
        self.calibration.scale_percent = 100
        self.calibration.offset_x = 0
        self.calibration.offset_y = 0
        if self.current_frame is not None:
            self._refresh_previews(self.current_frame)

    def save_calibration_action(self) -> None:
        save_calibration(self.calibration_path, self.calibration)
        self.status_label.setText(f"校准已保存：{self.calibration_path}")

    def _camera_index_changed(self, value: int) -> None:
        self.calibration.camera_index = value

    def closeEvent(self, event) -> None:  # noqa: N802
        self.timer.stop()
        self.stop_camera()
        save_calibration(self.calibration_path, self.calibration)
        if self._cast_dialog is not None:
            self._cast_dialog.close()
        super().closeEvent(event)


class ARImagingAdjustmentWindow(ARImagingAdjustmentWidget):
    """Top-level window for button 05."""
