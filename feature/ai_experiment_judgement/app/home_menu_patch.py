# -*- coding: utf-8 -*-
"""Runtime home-menu patch: add buttons 05 and 06."""

from __future__ import annotations

import os
import re
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

from app.ai_experiment_llm_judgement import AIExperimentLLMJudgementWindow
from app.ar_imaging_adjustment import ARImagingAdjustmentWindow

PATCH_MARKER_05 = "AR_IMAGING_ADJUSTMENT_BUTTON_05"
PATCH_MARKER_06 = "AI_EXPERIMENT_LLM_BUTTON_06"
BUTTON_05_TEXT = "05 | AR成像调节"
BUTTON_06_TEXT = "06 | AI实验判断"
_LEGACY_BUTTON_05_TEXT = "05 | AI实验判断"
_NUMBERED_BUTTON_RE = re.compile(r"^\s*(\d{2})\s*\|")
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
    _clear_stale_markers(main_window)

    menu_buttons: Tuple[Tuple[str, str, Callable[[QWidget, QWidget], None]], ...] = (
        (PATCH_MARKER_05, BUTTON_05_TEXT, _open_ar_imaging_adjustment),
        (PATCH_MARKER_06, BUTTON_06_TEXT, _open_ai_experiment_llm_judgement),
    )

    legacy = _find_button_by_text(main_window, _LEGACY_BUTTON_05_TEXT)
    if legacy is not None and isinstance(legacy, QPushButton):
        legacy.setText(BUTTON_05_TEXT)

    stack = _find_menu_button_stack(main_window)
    if stack is not None:
        return _install_into_stack(main_window, stack, menu_buttons)

    anchor = _find_anchor_button(main_window)
    if anchor is None:
        _log("anchor button 04 not found")
        return False

    changed = False
    current_anchor = anchor
    for marker, text, opener in menu_buttons:
        if _ensure_button(main_window, current_anchor, marker, text, opener):
            changed = True
            current_anchor = _find_button_by_text(main_window, text) or current_anchor
    return changed


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


install_ai_experiment_menu_button = install_home_menu_buttons


def _clear_stale_markers(main_window: QWidget) -> None:
    for marker, text in (
        (PATCH_MARKER_05, BUTTON_05_TEXT),
        (PATCH_MARKER_06, BUTTON_06_TEXT),
    ):
        if getattr(main_window, marker, False) and not _button_text_exists(main_window, text):
            setattr(main_window, marker, False)


def _install_into_stack(
    main_window: QWidget,
    stack: Tuple[QWidget, QLayout, List[QWidget], int],
    menu_buttons: Tuple[Tuple[str, str, Callable[[QWidget, QWidget], None]], ...],
) -> bool:
    stack_parent, layout, stack_buttons, _last_index = stack
    style_anchor = stack_buttons[-1]
    changed = False
    insert_after = _last_stack_index(layout, stack_buttons)
    if insert_after < 0:
        insert_after = max(0, layout.count() - 1)

    for marker, text, opener in menu_buttons:
        existing = _find_button_by_text(main_window, text)
        if existing is not None and isinstance(existing, QPushButton):
            insert_after = _move_button_into_stack(
                existing,
                stack_parent,
                layout,
                style_anchor,
                insert_after,
            )
            _rewire_button(existing, opener, main_window)
            existing.show()
            setattr(main_window, marker, True)
            changed = True
            continue
        if _insert_into_stack(
            main_window,
            stack_parent,
            layout,
            style_anchor,
            insert_after,
            marker,
            text,
            opener,
        ):
            insert_after += 1
            changed = True
    return changed


def _ensure_button(
    main_window: QWidget,
    anchor: QWidget,
    marker: str,
    text: str,
    opener: Callable[[QWidget, QWidget], None],
) -> bool:
    existing = _find_button_by_text(main_window, text)
    if existing is not None and isinstance(existing, QPushButton):
        _rewire_button(existing, opener, main_window)
        existing.show()
        setattr(main_window, marker, True)
        return True

    return _insert_after_anchor(main_window, anchor, marker, text, opener)


def _insert_into_stack(
    main_window: QWidget,
    stack_parent: QWidget,
    layout: QLayout,
    style_anchor: QWidget,
    insert_after: int,
    marker: str,
    text: str,
    opener: Callable[[QWidget, QWidget], None],
) -> bool:
    button = QPushButton(text, stack_parent)
    button.setObjectName(marker.lower())
    _match_button_geometry(style_anchor, button)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(_button_style(style_anchor))
    _rewire_button(button, opener, main_window)

    if not _insert_button_at(layout, insert_after + 1, button):
        button.deleteLater()
        _log(f"failed stack insert for {text}")
        return False

    button.show()
    setattr(main_window, marker, True)
    _log(f"inserted {text} into stack")
    return True


def _insert_after_anchor(
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
    _rewire_button(button, opener, main_window)

    layout, index = _find_layout_for_widget(anchor)
    if layout is not None and index >= 0 and _insert_button_at(layout, index + 1, button):
        button.show()
        setattr(main_window, marker, True)
        _log(f"inserted {text} via anchor layout")
        return True

    if _insert_button_by_geometry(anchor, button):
        button.show()
        button.raise_()
        setattr(main_window, marker, True)
        _log(f"inserted {text} via geometry")
        return True

    button.deleteLater()
    _log(f"failed to insert {text}")
    return False


def _move_button_into_stack(
    button: QPushButton,
    stack_parent: QWidget,
    layout: QLayout,
    style_anchor: QWidget,
    insert_after: int,
) -> int:
    _match_button_geometry(style_anchor, button)
    target_index = insert_after + 1

    current_index = layout.indexOf(button)
    if button.parentWidget() == stack_parent and current_index >= 0:
        if current_index != target_index:
            _remove_from_layout(layout, button)
            if _insert_button_at(layout, target_index, button):
                return target_index
            _insert_button_at(layout, current_index, button)
            return current_index
        return current_index

    old_parent = button.parentWidget()
    old_layout = old_parent.layout() if old_parent is not None else None
    button.setParent(stack_parent)
    if not _insert_button_at(layout, target_index, button):
        if old_parent is not None:
            button.setParent(old_parent)
            if old_layout is not None:
                _insert_button_at(old_layout, max(0, old_layout.count()), button)
        return insert_after

    if old_layout is not None and old_parent is not stack_parent:
        _remove_from_layout(old_layout, button)
    return target_index


def _remove_from_layout(layout: QLayout, widget: QWidget) -> None:
    if isinstance(layout, QBoxLayout):
        layout.removeWidget(widget)
        return
    if isinstance(layout, QGridLayout):
        layout.removeWidget(widget)
        return
    if hasattr(layout, "removeWidget"):
        layout.removeWidget(widget)  # type: ignore[attr-defined]


def _insert_button_at(layout: QLayout, index: int, button: QPushButton) -> bool:
    index = max(0, min(index, layout.count()))
    if isinstance(layout, QBoxLayout):
        layout.insertWidget(index, button)
        return True
    if isinstance(layout, QGridLayout):
        if layout.count() == 0:
            layout.addWidget(button, 0, 0)
            return True
        last_item = layout.itemAt(layout.count() - 1)
        if last_item is None or last_item.widget() is None:
            return False
        row, column, row_span, column_span = layout.getItemPosition(layout.count() - 1)
        layout.addWidget(button, row + row_span, column, row_span, column_span)
        return True
    if hasattr(layout, "insertWidget"):
        layout.insertWidget(index, button)  # type: ignore[attr-defined]
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


def _last_stack_index(layout: QLayout, stack_buttons: List[QWidget]) -> int:
    last_index = -1
    for button in stack_buttons:
        index = layout.indexOf(button)
        if index > last_index:
            last_index = index
    return last_index


def _find_menu_button_stack(
    root: QWidget,
) -> Optional[Tuple[QWidget, QLayout, List[QWidget], int]]:
    numbered_by_parent: dict[QWidget, List[QWidget]] = {}
    for widget in _iter_clickable_widgets(root):
        number = _button_number(widget)
        if number is None or number > 4:
            continue
        parent = widget.parentWidget()
        if parent is None:
            continue
        numbered_by_parent.setdefault(parent, []).append(widget)

    best_parent: Optional[QWidget] = None
    best_buttons: List[QWidget] = []
    for _parent, buttons in numbered_by_parent.items():
        unique = _unique_buttons_sorted(buttons)
        if len(unique) > len(best_buttons):
            best_parent = _parent
            best_buttons = unique

    if best_parent is None or len(best_buttons) < 3:
        return None

    layout = best_parent.layout()
    if layout is None:
        return None

    last_index = _last_stack_index(layout, best_buttons)
    if last_index < 0:
        last_index = max(0, layout.count() - 1)
    return best_parent, layout, best_buttons, last_index


def _find_anchor_button(root: QWidget) -> Optional[QWidget]:
    for widget in _iter_clickable_widgets(root):
        text = _widget_label_text(widget)
        compact = text.replace(" ", "")
        if "光学小实验" in text or compact.startswith("04|"):
            return widget
    numbered: List[QWidget] = []
    for widget in _iter_clickable_widgets(root):
        number = _button_number(widget)
        if number is not None and number <= 4:
            numbered.append(widget)
    if not numbered:
        return None
    return max(numbered, key=lambda item: _button_number(item) or 0)


def _unique_buttons_sorted(buttons: List[QWidget]) -> List[QWidget]:
    seen = set()
    unique: List[QWidget] = []
    for button in sorted(buttons, key=lambda item: _button_number(item) or 99):
        obj_id = id(button)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        unique.append(button)
    return unique


def _button_number(widget: QWidget) -> Optional[int]:
    match = _NUMBERED_BUTTON_RE.match(_widget_label_text(widget))
    if not match:
        return None
    return int(match.group(1))


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


def _match_button_geometry(anchor: QWidget, button: QPushButton) -> None:
    button.setSizePolicy(anchor.sizePolicy())
    button.setMinimumSize(anchor.minimumSize())
    button.setMaximumSize(anchor.maximumSize())
    if anchor.width() > 0 and anchor.height() > 0:
        button.setFixedSize(anchor.size())
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


def _rewire_button(
    button: QPushButton,
    opener: Callable[[QWidget, QWidget], None],
    main_window: QWidget,
) -> None:
    try:
        button.clicked.disconnect()
    except RuntimeError:
        pass
    button.clicked.connect(lambda: opener(main_window, button))


def _button_text_exists(root: QWidget, text: str) -> bool:
    return _find_button_by_text(root, text) is not None


def _find_button_by_text(root: QWidget, text: str) -> Optional[QWidget]:
    compact_target = text.replace(" ", "")
    for widget in _iter_clickable_widgets(root):
        if _widget_label_text(widget).replace(" ", "") == compact_target:
            return widget
    return None


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
        if _NUMBERED_BUTTON_RE.match(label.text()) or "实验" in label.text():
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
