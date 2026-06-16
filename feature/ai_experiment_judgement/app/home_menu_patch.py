# -*- coding: utf-8 -*-
"""Runtime home-menu patch: add the 05 | AI实验判断 button."""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QBoxLayout,
    QGridLayout,
    QLabel,
    QLayout,
    QPushButton,
    QWidget,
)

from app.ai_experiment_judgement import AIExperimentJudgementWindow

PATCH_MARKER = "AI_EXPERIMENT_JUDGEMENT_BUTTON_05"
BUTTON_TEXT = "05 | AI实验判断"
_RUNTIME_HOOKED = False
_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Creolight",
    "AR_Camera_Ollama",
    "home_menu_patch.log",
)


def activate_menu_patch_runtime() -> None:
    """Hook QApplication startup so desktop shortcuts also get button 05."""
    global _RUNTIME_HOOKED
    if _RUNTIME_HOOKED:
        return

    original_init = QApplication.__init__

    def patched_init(app_self, *args, **kwargs):
        original_init(app_self, *args, **kwargs)
        _install_show_event_filter()
        for delay_ms in (0, 100, 250, 500, 1000, 2000, 3500, 5000):
            QTimer.singleShot(delay_ms, install_on_top_level_window)

    QApplication.__init__ = patched_init  # type: ignore[method-assign]
    _RUNTIME_HOOKED = True
    _log("runtime hook activated")


def install_ai_experiment_menu_button(main_window: QWidget) -> bool:
    """Insert button 05 below the existing optics experiment button."""
    if getattr(main_window, PATCH_MARKER, False):
        return True

    if _button_already_exists(main_window):
        setattr(main_window, PATCH_MARKER, True)
        _log(f"button already exists on {type(main_window).__name__}")
        return True

    anchor = _find_anchor_button(main_window)
    if anchor is None:
        _log(f"anchor button not found on {type(main_window).__name__}")
        return False

    parent = anchor.parentWidget() or main_window
    button = QPushButton(BUTTON_TEXT, parent)
    button.setObjectName("btn_ai_experiment_judgement")
    button.setMinimumHeight(max(anchor.minimumHeight(), 72))
    button.setMinimumWidth(max(anchor.minimumWidth(), 320))
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(_button_style(anchor))
    button.clicked.connect(lambda: _open_ai_experiment_judgement(main_window))

    layout, index = _find_layout_for_widget(anchor)
    if layout is not None and index >= 0 and _insert_button_after(layout, index, button):
        button.show()
        setattr(main_window, PATCH_MARKER, True)
        _log(f"inserted button via layout on {type(main_window).__name__}")
        return True

    if _insert_button_by_geometry(anchor, button):
        button.show()
        button.raise_()
        setattr(main_window, PATCH_MARKER, True)
        _log(f"inserted button via geometry on {type(main_window).__name__}")
        return True

    _log(f"failed to insert button on {type(main_window).__name__}")
    return False


def schedule_ai_experiment_menu_button(main_window: QWidget) -> None:
    """Run after the home page layout is ready."""

    def _try_install() -> None:
        if install_ai_experiment_menu_button(main_window):
            return
        QTimer.singleShot(250, _try_install)

    QTimer.singleShot(0, _try_install)


def install_on_top_level_window() -> bool:
    app = QApplication.instance()
    if app is None:
        return False

    installed = False
    for widget in app.allWidgets():
        if not widget.isVisible():
            continue
        if widget.parentWidget() is not None and not widget.isWindow():
            continue
        if install_ai_experiment_menu_button(widget):
            installed = True
    return installed


class _ShowEventInstaller(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Show and isinstance(watched, QWidget):
            QTimer.singleShot(0, lambda w=watched: install_ai_experiment_menu_button(w))
        return False


def _install_show_event_filter() -> None:
    app = QApplication.instance()
    if app is None:
        return
    installer = getattr(app, "_ai_experiment_show_installer", None)
    if installer is None:
        installer = _ShowEventInstaller(app)
        app.installEventFilter(installer)
        setattr(app, "_ai_experiment_show_installer", installer)


def _button_already_exists(root: QWidget) -> bool:
    for button in _iter_clickable_widgets(root):
        text = _widget_label_text(button)
        if "AI实验判断" in text or text.replace(" ", "").startswith("05|"):
            return True
    return False


def _find_anchor_button(root: QWidget) -> Optional[QWidget]:
    candidates: List[QWidget] = []

    for widget in _iter_clickable_widgets(root):
        text = _widget_label_text(widget)
        compact = text.replace(" ", "")
        if "光学小实验" in text or compact.startswith("04|"):
            candidates.append(widget)

    if not candidates:
        numbered: List[QWidget] = []
        for widget in _iter_clickable_widgets(root):
            stripped = _widget_label_text(widget).strip()
            if len(stripped) >= 2 and stripped[:2].isdigit() and "|" in stripped:
                numbered.append(widget)
        if numbered:
            candidates = [max(numbered, key=lambda item: _widget_label_text(item))]

    if not candidates:
        return None
    return max(candidates, key=lambda item: len(_widget_label_text(item)))


def _iter_clickable_widgets(root: QWidget) -> List[QWidget]:
    widgets: List[QWidget] = []
    seen = set()

    for button in root.findChildren(QAbstractButton):
        obj_id = id(button)
        if obj_id not in seen:
            seen.add(obj_id)
            widgets.append(button)

    for label in root.findChildren(QLabel):
        if not label.text().strip():
            continue
        if label.text().replace(" ", "")[:2].isdigit() or "实验" in label.text():
            obj_id = id(label)
            if obj_id not in seen:
                seen.add(obj_id)
                widgets.append(label)

    return widgets


def _widget_label_text(widget: QWidget) -> str:
    if isinstance(widget, QAbstractButton):
        return widget.text()
    if isinstance(widget, QLabel):
        return widget.text()
    return ""


def _find_layout_for_widget(widget: QWidget) -> Tuple[Optional[QLayout], int]:
    current = widget
    while current is not None:
        parent = current.parentWidget()
        if parent is None:
            break
        layout = parent.layout()
        if layout is not None:
            index = layout.indexOf(current)
            if index >= 0:
                return layout, index
        current = parent
    return None, -1


def _insert_button_after(layout: QLayout, index: int, button: QPushButton) -> bool:
    if isinstance(layout, QBoxLayout):
        layout.insertWidget(index + 1, button)
        return True

    if isinstance(layout, QGridLayout):
        anchor_item = layout.itemAt(index)
        if anchor_item is None or anchor_item.widget() is None:
            return False
        row, column, row_span, column_span = layout.getItemPosition(index)
        layout.addWidget(button, row + row_span, column, row_span, column_span)
        return True

    if hasattr(layout, "insertWidget"):
        layout.insertWidget(index + 1, button)  # type: ignore[attr-defined]
        return True

    return False


def _insert_button_by_geometry(anchor: QWidget, button: QPushButton) -> bool:
    parent = anchor.parentWidget()
    if parent is None:
        return False

    anchor_geo = anchor.geometry()
    if anchor_geo.width() <= 0 or anchor_geo.height() <= 0:
        return False

    spacing = 12
    button.setGeometry(
        anchor_geo.x(),
        anchor_geo.y() + anchor_geo.height() + spacing,
        anchor_geo.width(),
        anchor_geo.height(),
    )
    return True


def _button_style(anchor: QWidget) -> str:
    anchor_style = anchor.styleSheet().strip()
    if anchor_style:
        return anchor_style
    return (
        "QPushButton {"
        "color: #1f2937;"
        "font-size: 22px;"
        "font-weight: 600;"
        "text-align: left;"
        "padding: 18px 28px;"
        "border: 1px solid #c4b5fd;"
        "border-radius: 18px;"
        "background: qlineargradient("
        "x1:0, y1:0, x2:0, y2:1,"
        "stop:0 #ddd6fe, stop:1 #a78bfa"
        ");"
        "}"
        "QPushButton:hover {"
        "background: qlineargradient("
        "x1:0, y1:0, x2:0, y2:1,"
        "stop:0 #ede9fe, stop:1 #c4b5fd"
        ");"
        "}"
    )


def _open_ai_experiment_judgement(main_window: QWidget) -> None:
    existing = getattr(main_window, "_ai_experiment_judgement_window", None)
    if existing is not None:
        existing.show()
        existing.raise_()
        existing.activateWindow()
        return

    window = AIExperimentJudgementWindow()
    window.resize(1120, 820)
    window.show()
    setattr(main_window, "_ai_experiment_judgement_window", window)


def _log(message: str) -> None:
    if not _LOG_PATH:
        return
    try:
        log_dir = os.path.dirname(_LOG_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass
