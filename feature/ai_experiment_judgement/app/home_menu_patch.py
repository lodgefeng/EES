# -*- coding: utf-8 -*-
"""Runtime home-menu patch: add buttons 05 and 06."""

from __future__ import annotations

import os
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QBoxLayout,
    QGridLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from app.ar_imaging_adjustment import ARImagingAdjustmentWindow
from app.ai_experiment_llm_judgement import AIExperimentLLMJudgementWindow

PATCH_MARKER_05 = "AR_IMAGING_ADJUSTMENT_BUTTON_05"
PATCH_MARKER_06 = "AI_EXPERIMENT_LLM_BUTTON_06"
BUTTON_05_TEXT = "05 | AR成像调节"
BUTTON_06_TEXT = "06 | AI实验判断"
_RUNTIME_HOOKED = False
_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Creolight",
    "AR_Camera_Ollama",
    "home_menu_patch.log",
)


def activate_menu_patch_runtime() -> None:
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


def install_home_menu_buttons(main_window: QWidget) -> bool:
    menu_buttons: Tuple[Tuple[str, str, Callable[[QWidget, QWidget], None]], ...] = (
        (PATCH_MARKER_05, BUTTON_05_TEXT, _open_ar_imaging_adjustment),
        (PATCH_MARKER_06, BUTTON_06_TEXT, _open_ai_experiment_llm_judgement),
    )
    anchor = _find_anchor_button(main_window)
    if anchor is None:
        return False

    legacy_button = _find_button_by_text(main_window, "05 | AI实验判断")
    if legacy_button is not None and isinstance(legacy_button, QPushButton):
        legacy_button.setText(BUTTON_05_TEXT)
        _match_button_geometry(anchor, legacy_button)
        legacy_button.clicked.disconnect()
        legacy_button.clicked.connect(
            lambda: _open_ar_imaging_adjustment(main_window, legacy_button)
        )
        setattr(main_window, PATCH_MARKER_05, True)

    inserted_any = False
    current_anchor = anchor
    for marker, text, opener in menu_buttons:
        if getattr(main_window, marker, False):
            current_anchor = _find_button_by_text(main_window, text) or current_anchor
            continue
        if _button_text_exists(main_window, text):
            setattr(main_window, marker, True)
            current_anchor = _find_button_by_text(main_window, text) or current_anchor
            continue
        if _insert_menu_button(main_window, current_anchor, marker, text, opener):
            inserted_any = True
            current_anchor = _find_button_by_text(main_window, text) or current_anchor
    return inserted_any


def schedule_ai_experiment_menu_button(main_window: QWidget) -> None:
    def _try_install() -> None:
        if install_home_menu_buttons(main_window):
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
        if install_home_menu_buttons(widget):
            installed = True
    return installed


class _ShowEventInstaller(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Show and isinstance(watched, QWidget):
            QTimer.singleShot(0, lambda w=watched: install_home_menu_buttons(w))
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


# Backward-compatible alias used by older patch scripts.
install_ai_experiment_menu_button = install_home_menu_buttons


def _insert_menu_button(
    main_window: QWidget,
    anchor: QWidget,
    marker: str,
    text: str,
    opener: Callable[[QWidget, QWidget], None],
) -> bool:
    parent = anchor.parentWidget() or main_window
    button = QPushButton(text, parent)
    button.setObjectName(marker.lower())
    _match_button_geometry(anchor, button)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(_button_style(anchor))
    button.clicked.connect(lambda: opener(main_window, button))

    layout, index = _find_layout_for_widget(anchor)
    if layout is not None and index >= 0 and _insert_button_after(layout, index, button):
        button.show()
        setattr(main_window, marker, True)
        _log(f"inserted {text} via layout")
        return True

    if _insert_button_by_geometry(anchor, button):
        button.show()
        button.raise_()
        setattr(main_window, marker, True)
        _log(f"inserted {text} via geometry")
        return True

    _log(f"failed to insert {text}")
    return False


def _match_button_geometry(anchor: QWidget, button: QPushButton) -> None:
    button.setSizePolicy(anchor.sizePolicy())
    if anchor.minimumWidth() > 0:
        button.setMinimumWidth(anchor.minimumWidth())
    if anchor.maximumWidth() < 16777215:
        button.setMaximumWidth(anchor.maximumWidth())
    if anchor.minimumHeight() > 0:
        button.setMinimumHeight(anchor.minimumHeight())
    if anchor.maximumHeight() < 16777215:
        button.setMaximumHeight(anchor.maximumHeight())
    if anchor.width() > 0:
        button.setFixedWidth(anchor.width())
    if anchor.height() > 0:
        button.setFixedHeight(anchor.height())
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


def _button_text_exists(root: QWidget, text: str) -> bool:
    compact_target = text.replace(" ", "")
    for widget in _iter_clickable_widgets(root):
        compact = _widget_label_text(widget).replace(" ", "")
        if compact == compact_target:
            return True
    return False


def _find_button_by_text(root: QWidget, text: str) -> Optional[QWidget]:
    compact_target = text.replace(" ", "")
    for widget in _iter_clickable_widgets(root):
        if _widget_label_text(widget).replace(" ", "") == compact_target:
            return widget
    return None


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


def _open_ar_imaging_adjustment(main_window: QWidget, _button: QWidget) -> None:
    existing = getattr(main_window, "_ar_imaging_adjustment_window", None)
    if existing is not None:
        main_window.hide()
        existing.home_window = main_window
        existing.show()
        existing.raise_()
        existing.activateWindow()
        return
    window = ARImagingAdjustmentWindow(home_window=main_window)
    window.resize(1280, 860)
    main_window.hide()
    window.show()
    setattr(main_window, "_ar_imaging_adjustment_window", window)


def _open_ai_experiment_llm_judgement(main_window: QWidget, _button: QWidget) -> None:
    existing = getattr(main_window, "_ai_experiment_llm_window", None)
    if existing is not None:
        main_window.hide()
        existing.home_window = main_window
        existing.show()
        existing.raise_()
        existing.activateWindow()
        return
    window = AIExperimentLLMJudgementWindow(home_window=main_window)
    window.resize(1180, 900)
    main_window.hide()
    window.show()
    setattr(main_window, "_ai_experiment_llm_window", window)


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
