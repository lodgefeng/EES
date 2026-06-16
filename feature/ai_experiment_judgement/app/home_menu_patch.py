# -*- coding: utf-8 -*-
"""Runtime home-menu patch: add buttons 05 and 06."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

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
_PATCH_NUMBERS = (5, 6)
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

    legacy = _find_button_by_text(main_window, _LEGACY_BUTTON_05_TEXT)
    if legacy is not None:
        if isinstance(legacy, QPushButton):
            legacy.setText(BUTTON_05_TEXT)
        else:
            _destroy_widget(legacy)

    if _buttons_ready_and_aligned(main_window):
        return True

    stack = _find_menu_button_stack(main_window)
    if stack is None:
        for widget in _iter_patch_widgets(main_window):
            _destroy_widget(widget)
        _log("menu stack not found; will retry on next timer")
        return False

    stack_parent, layout, stack_buttons, insert_after = stack
    style_anchor = stack_buttons[-1]

    _remove_misplaced_patch_widgets(main_window, layout)

    menu_buttons: Tuple[Tuple[str, str, Callable[[QWidget, QWidget], None]], ...] = (
        (PATCH_MARKER_05, BUTTON_05_TEXT, _open_ar_imaging_adjustment),
        (PATCH_MARKER_06, BUTTON_06_TEXT, _open_ai_experiment_llm_judgement),
    )

    changed = False
    next_index = insert_after + 1
    for marker, text, opener in menu_buttons:
        existing = _find_menu_button(main_window, text)
        if existing is not None:
            if layout.indexOf(existing) >= 0:
                next_index = _ensure_button_in_layout(
                    existing, stack_parent, layout, style_anchor, next_index
                )
                _rewire_button(existing, opener, main_window)
                existing.show()
                setattr(main_window, marker, True)
                changed = True
                continue
            _destroy_widget(existing)

        if _insert_into_stack(
            main_window,
            stack_parent,
            layout,
            style_anchor,
            next_index,
            marker,
            text,
            opener,
        ):
            next_index += 1
            changed = True

    ready = _buttons_ready_and_aligned(main_window)
    if ready:
        _log("home menu buttons 05/06 ready")
    else:
        _log("home menu buttons 05/06 still missing after install")
    return changed or ready


def _buttons_ready_and_aligned(main_window: QWidget) -> bool:
    stack = _find_menu_button_stack(main_window)
    if stack is None:
        return False
    _, layout, stack_buttons, _ = stack
    stack_numbers = {_button_number(button) for button in stack_buttons}
    if not {1, 4}.issubset(stack_numbers):
        return False
    for text in (BUTTON_05_TEXT, BUTTON_06_TEXT):
        button = _find_menu_button(main_window, text)
        if button is None:
            return False
        if not button.isVisible():
            return False
        if layout.indexOf(button) < 0:
            return False
    return True


def _ensure_button_in_layout(
    button: QPushButton,
    stack_parent: QWidget,
    layout: QLayout,
    style_anchor: QWidget,
    insert_index: int,
) -> int:
    _match_button_geometry(style_anchor, button)
    owner = _layout_owner(layout) or stack_parent
    if button.parentWidget() is not owner:
        button.setParent(owner)
    current_index = layout.indexOf(button)
    if current_index >= 0:
        return max(current_index, insert_index)
    if _insert_button_at(layout, insert_index, button):
        return insert_index
    return insert_index


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
    for widget in app.topLevelWidgets():
        if not widget.isVisible():
            continue
        if install_home_menu_buttons(widget):
            installed = True
    return installed


class _ShowEventInstaller(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Show and isinstance(watched, QWidget):
            if watched.isWindow():
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


def _buttons_ready(main_window: QWidget) -> bool:
    return (
        _find_menu_button(main_window, BUTTON_05_TEXT) is not None
        and _find_menu_button(main_window, BUTTON_06_TEXT) is not None
    )


def _clear_stale_markers(main_window: QWidget) -> None:
    for marker, text in (
        (PATCH_MARKER_05, BUTTON_05_TEXT),
        (PATCH_MARKER_06, BUTTON_06_TEXT),
    ):
        if getattr(main_window, marker, False) and not _button_text_exists(main_window, text):
            setattr(main_window, marker, False)


def _remove_misplaced_patch_widgets(root: QWidget, target_layout: QLayout) -> None:
    for widget in _iter_patch_widgets(root):
        if target_layout.indexOf(widget) >= 0:
            continue
        _destroy_widget(widget)


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


def _iter_patch_widgets(root: QWidget) -> List[QWidget]:
    widgets: List[QWidget] = []
    for widget in _iter_clickable_widgets(root):
        number = _button_number(widget)
        if number in _PATCH_NUMBERS:
            widgets.append(widget)
            continue
        text = _widget_label_text(widget).replace(" ", "")
        if text in {
            BUTTON_05_TEXT.replace(" ", ""),
            BUTTON_06_TEXT.replace(" ", ""),
            _LEGACY_BUTTON_05_TEXT.replace(" ", ""),
        }:
            widgets.append(widget)
    return widgets


def _destroy_widget(widget: QWidget) -> None:
    parent = widget.parentWidget()
    if parent is not None:
        layout = parent.layout()
        if layout is not None:
            _remove_from_layout(layout, widget)
    widget.hide()
    widget.deleteLater()
    _log(f"removed duplicate patch widget: {_widget_label_text(widget)}")


def _insert_into_stack(
    main_window: QWidget,
    stack_parent: QWidget,
    layout: QLayout,
    style_anchor: QWidget,
    insert_index: int,
    marker: str,
    text: str,
    opener: Callable[[QWidget, QWidget], None],
) -> bool:
    owner = _layout_owner(layout) or stack_parent
    button = QPushButton(text, owner)
    button.setObjectName(marker.lower())
    _match_button_geometry(style_anchor, button)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(_button_style(style_anchor))
    _rewire_button(button, opener, main_window)

    if not _insert_button_at(layout, insert_index, button):
        button.deleteLater()
        _log(f"failed stack insert for {text}")
        return False

    button.show()
    setattr(main_window, marker, True)
    _log(f"inserted {text} into stack at {insert_index}")
    return True


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


def _layout_owner(layout: QLayout) -> Optional[QWidget]:
    owner = layout.parentWidget()
    if owner is not None:
        return owner
    parent = layout.parent()
    return parent if isinstance(parent, QWidget) else None


def _last_stack_index(layout: QLayout, stack_buttons: List[QWidget]) -> int:
    last_index = -1
    for button in stack_buttons:
        index = layout.indexOf(button)
        if index > last_index:
            last_index = index
    return last_index


def _group_menu_buttons_by_layout(
    root: QWidget,
) -> Dict[QLayout, List[QWidget]]:
    grouped: Dict[QLayout, List[QWidget]] = defaultdict(list)
    for widget in _iter_menu_label_widgets(root):
        number = _button_number(widget)
        if number is None or number > 4:
            continue
        layout, index = _find_layout_for_widget(widget)
        if layout is None or index < 0:
            continue
        grouped[layout].append(widget)
    return grouped


def _find_menu_button_stack(
    root: QWidget,
) -> Optional[Tuple[QWidget, QLayout, List[QWidget], int]]:
    grouped = _group_menu_buttons_by_layout(root)
    if not grouped:
        _log("no numbered home-menu layouts found")
        return None

    best_layout: Optional[QLayout] = None
    best_buttons: List[QWidget] = []
    for layout, buttons in grouped.items():
        unique = _unique_buttons_sorted(buttons)
        if len(unique) > len(best_buttons):
            best_layout = layout
            best_buttons = unique

    if best_layout is None or len(best_buttons) < 2:
        _log("home-menu layout has too few numbered buttons")
        return None

    stack_numbers = {_button_number(button) for button in best_buttons}
    if 1 not in stack_numbers or 4 not in stack_numbers:
        anchor = _find_anchor_button(root)
        if anchor is None:
            _log("home-menu layout missing buttons 01 and 04")
            return None
        layout, anchor_index = _find_layout_for_widget(anchor)
        if layout is None or anchor_index < 0:
            _log("anchor button 04 is not inside a layout")
            return None
        best_layout = layout
        best_buttons = _unique_buttons_sorted(
            [
                widget
                for widget in _iter_menu_label_widgets(root)
                if _button_number(widget) is not None
                and (_button_number(widget) or 99) <= 4
                and layout.indexOf(widget) >= 0
            ]
        )
        if len(best_buttons) < 2:
            _log("anchor fallback layout still has too few buttons")
            return None

    stack_parent = _layout_owner(best_layout)
    if stack_parent is None:
        stack_parent = best_buttons[-1].parentWidget()
    if stack_parent is None:
        _log("home-menu stack parent not found")
        return None

    last_index = _last_stack_index(best_layout, best_buttons)
    if last_index < 0:
        _log("home-menu buttons are not direct layout children")
        return None

    numbers = sorted(_button_number(button) or 0 for button in best_buttons)
    _log(
        "home-menu stack found: parent="
        f"{stack_parent.__class__.__name__}, buttons={numbers}, insert_after={last_index}"
    )
    return stack_parent, best_layout, best_buttons, last_index


def _find_anchor_button(root: QWidget) -> Optional[QWidget]:
    for widget in _iter_menu_label_widgets(root):
        text = _widget_label_text(widget)
        compact = text.replace(" ", "")
        if "光学小实验" in text or compact.startswith("04|"):
            return widget
    numbered: List[QWidget] = []
    for widget in _iter_menu_label_widgets(root):
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
    return _find_menu_button(root, text) is not None


def _find_menu_button(root: QWidget, text: str) -> Optional[QPushButton]:
    compact_target = text.replace(" ", "")
    for button in root.findChildren(QPushButton):
        if _widget_label_text(button).replace(" ", "") == compact_target:
            return button
    return None


def _find_button_by_text(root: QWidget, text: str) -> Optional[QWidget]:
    button = _find_menu_button(root, text)
    if button is not None:
        return button
    compact_target = text.replace(" ", "")
    for widget in _iter_menu_label_widgets(root):
        if _widget_label_text(widget).replace(" ", "") == compact_target:
            return widget
    return None


def _iter_menu_label_widgets(root: QWidget) -> List[QWidget]:
    widgets: List[QWidget] = []
    seen = set()
    for button in root.findChildren(QAbstractButton):
        text = _widget_label_text(button)
        if not _NUMBERED_BUTTON_RE.match(text):
            continue
        obj_id = id(button)
        if obj_id not in seen:
            seen.add(obj_id)
            widgets.append(button)
    for label in root.findChildren(QLabel):
        text = label.text().strip()
        if not text or not _NUMBERED_BUTTON_RE.match(text):
            continue
        obj_id = id(label)
        if obj_id not in seen:
            seen.add(obj_id)
            widgets.append(label)
    return widgets


def _iter_clickable_widgets(root: QWidget) -> List[QWidget]:
    return _iter_menu_label_widgets(root)


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
    return ""


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
