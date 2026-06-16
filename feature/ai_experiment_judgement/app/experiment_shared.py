# -*- coding: utf-8 -*-
"""Shared helpers for AR imaging and AI experiment judgement pages."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

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


def default_config_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "Creolight" / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def load_calibration(path: Path) -> OverlayCalibration:
    if not path.exists():
        return OverlayCalibration()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return OverlayCalibration(**data)
    except Exception:  # noqa: BLE001
        return OverlayCalibration()


def save_calibration(path: Path, calibration: OverlayCalibration) -> None:
    path.write_text(
        json.dumps(asdict(calibration), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_image(path: Path) -> Optional[np.ndarray]:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    return image


def write_image(path: Path, image: np.ndarray) -> None:
    cv2.imwrite(str(path), image)


def compose_overlay(
    frame: np.ndarray,
    reference_image: Optional[np.ndarray],
    calibration: OverlayCalibration,
    alpha: float = 0.42,
) -> np.ndarray:
    if reference_image is None:
        return frame.copy()
    canvas = frame.copy()
    transformed, mask = reference_canvas(frame.shape[:2], reference_image, calibration)
    if transformed is None or mask is None:
        return canvas
    overlay_area = mask > 0
    canvas[overlay_area] = cv2.addWeighted(
        canvas[overlay_area],
        1.0 - alpha,
        transformed[overlay_area],
        alpha,
        0,
    )
    return canvas


def reference_canvas(
    frame_hw: Tuple[int, int],
    reference_image: np.ndarray,
    calibration: OverlayCalibration,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    frame_h, frame_w = frame_hw
    ref_h, ref_w = reference_image.shape[:2]
    scale = max(1, calibration.scale_percent) / 100.0
    new_w = max(1, int(ref_w * scale))
    new_h = max(1, int(ref_h * scale))
    resized = cv2.resize(reference_image, (new_w, new_h))

    x = int((frame_w - new_w) / 2 + calibration.offset_x)
    y = int((frame_h - new_h) / 2 + calibration.offset_y)

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


def reference_preview_image(
    frame_hw: Tuple[int, int],
    reference_image: Optional[np.ndarray],
    calibration: OverlayCalibration,
) -> np.ndarray:
    frame_h, frame_w = frame_hw
    if reference_image is None:
        return np.zeros((frame_h, frame_w, 3), dtype=np.uint8)
    canvas, _mask = reference_canvas(frame_hw, reference_image, calibration)
    return canvas


def similarity_score(
    frame: np.ndarray,
    reference_canvas_img: np.ndarray,
    mask: np.ndarray,
) -> float:
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(reference_canvas_img, cv2.COLOR_BGR2GRAY)
    valid = mask > 0
    if np.count_nonzero(valid) < 100:
        return 0.0
    diff = cv2.absdiff(frame_gray, ref_gray)
    pixel_score = 100.0 * (1.0 - float(np.mean(diff[valid])) / 255.0)
    frame_edge = cv2.Canny(frame_gray, 80, 160)
    ref_edge = cv2.Canny(ref_gray, 80, 160)
    edge_diff = cv2.absdiff(frame_edge, ref_edge)
    edge_score = 100.0 * (1.0 - float(np.mean(edge_diff[valid])) / 255.0)
    return max(0.0, min(100.0, pixel_score * 0.7 + edge_score * 0.3))


def find_difference_regions(
    frame: np.ndarray,
    reference_canvas_img: np.ndarray,
    mask: np.ndarray,
    min_area: int = 500,
) -> list[Tuple[int, int, int]]:
    """Return list of (x, y, radius) circles for visible differences."""
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(reference_canvas_img, cv2.COLOR_BGR2GRAY)
    valid = mask > 0
    diff = cv2.absdiff(frame_gray, ref_gray)
    diff[~valid] = 0
    blurred = cv2.GaussianBlur(diff, (9, 9), 0)
    _, thresh = cv2.threshold(blurred, 35, 255, cv2.THRESH_BINARY)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    circles: list[Tuple[int, int, int]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        radius = max(12, int(max(w, h) * 0.65))
        circles.append((x + w // 2, y + h // 2, radius))
    return circles


def draw_difference_circles(
    frame: np.ndarray,
    circles: list[Tuple[int, int, int]],
) -> np.ndarray:
    output = frame.copy()
    for index, (cx, cy, radius) in enumerate(circles, start=1):
        color = (0, 80, 255)
        cv2.circle(output, (cx, cy), radius, color, 3)
        cv2.putText(
            output,
            str(index),
            (cx - 10, cy + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
            cv2.LINE_AA,
        )
    return output


def numpy_to_label_pixmap(image: np.ndarray, label: QLabel) -> QPixmap:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimage = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage).scaled(
        label.size(),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )


def show_frame_on_label(label: QLabel, image: np.ndarray) -> None:
    label.setPixmap(numpy_to_label_pixmap(image, label))


class CameraMixin:
    """Mixin for pages that read from an OpenCV camera."""

    camera: Optional[cv2.VideoCapture]
    current_frame: Optional[np.ndarray]

    def start_camera(self, camera_index: int) -> tuple[bool, str]:
        self.stop_camera()
        self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            self.camera = None
            return False, "Camera failed to start."
        return True, "Camera started."

    def stop_camera(self) -> None:
        if getattr(self, "camera", None) is not None:
            self.camera.release()
            self.camera = None

    def read_camera_frame(self) -> Optional[np.ndarray]:
        if self.camera is None:
            return None
        ok, frame = self.camera.read()
        if not ok:
            return None
        self.current_frame = frame
        return frame
