# -*- coding: utf-8 -*-
"""Optional JBD4020 control-board casting integration."""

from __future__ import annotations

from typing import Any, Callable, Optional

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.experiment_shared import show_frame_on_label


class JBD4020CastController:
    """Thin adapter around the real app JBD4020 service when available."""

    def __init__(self) -> None:
        self._service: Any = None
        self._last_error = ""
        self._load_service()

    @property
    def available(self) -> bool:
        return self._service is not None

    @property
    def last_error(self) -> str:
        return self._last_error

    def connect(self) -> bool:
        if self._service is None:
            self._last_error = "JBD4020 service module not found in app package."
            return False
        for method_name in ("connect", "open", "start"):
            method = getattr(self._service, method_name, None)
            if callable(method):
                try:
                    method()
                    return True
                except Exception as exc:  # noqa: BLE001
                    self._last_error = str(exc)
        self._last_error = "No connect/open/start method found on JBD4020 service."
        return False

    def disconnect(self) -> None:
        if self._service is None:
            return
        for method_name in ("disconnect", "close", "stop"):
            method = getattr(self._service, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:  # noqa: BLE001
                    pass
                return

    def cast_frame(self, frame: np.ndarray) -> bool:
        if self._service is None:
            self._last_error = "JBD4020 service not available."
            return False
        for method_name in (
            "cast_frame",
            "send_frame",
            "display_frame",
            "push_frame",
            "show_image",
            "display_image",
            "send_image",
        ):
            method = getattr(self._service, method_name, None)
            if callable(method):
                try:
                    method(frame)
                    return True
                except Exception as exc:  # noqa: BLE001
                    self._last_error = str(exc)
        self._last_error = "No compatible cast method found on JBD4020 service."
        return False

    def _load_service(self) -> None:
        candidates = (
            ("app.jbd4020_service", "get_jbd4020_service"),
            ("app.jbd4020_service", "JBD4020Service"),
            ("app.jbd4020_service", "jbd4020_service"),
            ("app.jbd4020_service", None),
        )
        for module_name, attr_name in candidates:
            try:
                module = __import__(module_name, fromlist=["*"])
            except Exception:  # noqa: BLE001
                continue
            if attr_name is None:
                self._service = module
                return
            obj = getattr(module, attr_name, None)
            if obj is None:
                continue
            self._service = obj() if isinstance(obj, type) else obj
            if callable(self._service) and not isinstance(self._service, type):
                try:
                    self._service = self._service()
                except Exception:  # noqa: BLE001
                    pass
            if self._service is not None:
                return


class JBD4020CastDialog(QDialog):
    """Popup to cast the reference preview stream to a 4020 control board."""

    def __init__(
        self,
        frame_provider: Callable[[], Optional[np.ndarray]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("4020 Control Board Cast")
        self._frame_provider = frame_provider
        self._controller = JBD4020CastController()
        self._casting = False

        self.preview_label = QLabel("No preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(480, 300)
        self.preview_label.setStyleSheet("background:#101820;color:#dbeafe;")

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        connect_button = QPushButton("Connect 4020")
        connect_button.clicked.connect(self._connect_board)

        self.cast_button = QPushButton("Start Cast")
        self.cast_button.clicked.connect(self._toggle_cast)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        button_row = QHBoxLayout()
        button_row.addWidget(connect_button)
        button_row.addWidget(self.cast_button)
        button_row.addStretch(1)
        button_row.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Cast the reference preview window to JBD4020 board:"))
        layout.addWidget(self.preview_label)
        layout.addLayout(button_row)
        layout.addWidget(self.status_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._refresh_status()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_cast()
        super().closeEvent(event)

    def _refresh_status(self) -> None:
        if self._controller.available:
            self.status_label.setText("JBD4020 service detected in app package.")
        else:
            self.status_label.setText(
                "JBD4020 service not found. Copy is still shown here; "
                "install app\\jbd4020_service.py on this machine to enable casting."
            )

    def _connect_board(self) -> None:
        if not self._controller.available:
            QMessageBox.warning(self, "4020", self._controller.last_error)
            return
        if self._controller.connect():
            self.status_label.setText("4020 board connected.")
        else:
            QMessageBox.warning(self, "4020", self._controller.last_error)

    def _toggle_cast(self) -> None:
        if self._casting:
            self._stop_cast()
            return
        if not self._controller.available:
            QMessageBox.warning(self, "4020", self._controller.last_error)
            return
        self._casting = True
        self.cast_button.setText("Stop Cast")
        self._timer.start(80)
        self.status_label.setText("Casting reference preview to 4020 board...")

    def _stop_cast(self) -> None:
        self._casting = False
        self._timer.stop()
        self.cast_button.setText("Start Cast")
        self._controller.disconnect()

    def _tick(self) -> None:
        frame = self._frame_provider()
        if frame is None:
            return
        show_frame_on_label(self.preview_label, frame)
        if self._casting:
            if not self._controller.cast_frame(frame):
                self.status_label.setText(self._controller.last_error)
