# -*- coding: utf-8 -*-
"""Runtime home-menu patch: add buttons 05 and 06."""

from __future__ import annotations

import os
import re
import traceback
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
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

PATCH_MARKER_05 = "AR_IMAGING_ADJUSTMENT_BUTTON_05"
PATCH_MARKER_06 = "AI_EXPERIMENT_LLM_BUTTON_06"
BUTTON_05_TEXT = "05 | AR成像调节"
BUTTON_06_TEXT = "06 | AI实验判断"
_LEGACY_BUTTON_05_TEXT = "05 | AI实验判断"
_NUMBERED_BUTTON_RE = re.compile(r"^\s*(\d{1,2})\s*[\|｜]")
_MENU_KEYWORDS: Dict[int, Tuple[str, ...]] = {
    1: ("万物识别", "01"),
    2: ("大模型翻译", "02"),
    3: ("实时显示", "03"),
    4: ("光学小实验", "04"),
}
_PATCH_NUMBERS = (5, 6)
_RUNTIME_HOOKED = False
_DUMPED_WIDGETS = False
_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Creolight",
    "AR_Camera_Ollama",
    "home_menu_patch.log",
)

LayoutStack = Tuple[QWidget, QLayout, List[QWidget], int]


@dataclass
class GeometryStack:
    parent: QWidget
    containers: List[Tuple[int, QWidget]]
    gap: int


def activate_menu_patch_runtime() -> None:
    global _RUNTIME_HOOKED
    if _RUNTIME_HOOKED:
        return

    original_init = QApplication.__init__

    def patched_init(app_self, *args, **kwargs):
        original_init(app_self, *args, **kwargs)
        _install_show_event_filter()
        for delay_ms in (0, 100, 250, 500, 1000, 2000, 3500, 5000, 8000, 12000, 18000):
            QTimer.singleShot(delay_ms, install_on_top_level_window)

    QApplication.__init__ = patched_init  # type: ignore[method-assign]
    _RUNTIME_HOOKED = True
    _log("runtime hook activated")


def install_home_menu_buttons(main_window: QWidget) -> bool:
    try:
        return _install_home_menu_buttons(main_window)
    except Exception:
        _log("install_home_menu_buttons failed")
        _log(traceback.format_exc())
        return False


def _install_home_menu_buttons(main_window: QWidget) -> bool:
    _clear_stale_markers(main_window)

    legacy = _find_button_by_text(main_window, _LEGACY_BUTTON_05_TEXT)
    if legacy is not None:
        if isinstance(legacy, QPushButton):
            legacy.setText(BUTTON_05_TEXT)
        else:
            _destroy_widget(legacy)

    if _buttons_ready_and_aligned(main_window):
        return True

    layout_stack = _find_menu_button_stack(main_window)
    if layout_stack is not None:
        return _install_layout_buttons(main_window, layout_stack)

    geometry_stack = _find_geometry_stack(main_window)
    if geometry_stack is not None:
        return _install_geometry_buttons(main_window, geometry_stack)

    for widget in _iter_patch_widgets(main_window):
        _destroy_widget(widget)
    _dump_menu_widgets_once(main_window)
    _log("menu stack not found; will retry on next timer")
    return False


def _install_layout_buttons(main_window: QWidget, stack: LayoutStack) -> bool:
    stack_parent, layout, stack_buttons, insert_after = stack
    style_anchor = _style_source_widget(stack_buttons[-1])
    _remove_misplaced_patch_widgets(main_window, layout)
    return _install_menu_buttons(
        main_window,
        style_anchor,
        layout_mode=(stack_parent, layout, insert_after + 1),
    )


def _install_geometry_buttons(main_window: QWidget, stack: GeometryStack) -> bool:
    _remove_misplaced_geometry_patch_widgets(main_window, stack.parent)
    anchor_container = stack.containers[-1][1]
    style_anchor = _style_source_widget(anchor_container)
    numbers = [number for number, _ in stack.containers]
    _log(
        "home-menu geometry stack found: parent="
        f"{stack.parent.__class__.__name__}, buttons={numbers}, gap={stack.gap}"
    )
    return _install_menu_buttons(
        main_window,
        style_anchor,
        geometry_mode=(stack.parent, stack.containers[-1][1], stack.gap),
    )


def _install_menu_buttons(
    main_window: QWidget,
    style_anchor: QWidget,
    *,
    layout_mode: Optional[Tuple[QWidget, QLayout, int]] = None,
    geometry_mode: Optional[Tuple[QWidget, QWidget, int]] = None,
) -> bool:
    menu_buttons: Tuple[Tuple[str, str, Callable[[QWidget, QWidget], None]], ...] = (
        (PATCH_MARKER_05, BUTTON_05_TEXT, _open_ar_imaging_adjustment),
        (PATCH_MARKER_06, BUTTON_06_TEXT, _open_ai_experiment_llm_judgement),
    )

    changed = False
    next_layout_index = layout_mode[2] if layout_mode is not None else 0
    next_geometry_y: Optional[int] = None

    if geometry_mode is not None:
        parent, anchor_container, gap = geometry_mode
        next_geometry_y = anchor_container.y() + anchor_container.height() + gap

    for marker, text, opener in menu_buttons:
        existing = _find_menu_button(main_window, text)
        if existing is not None:
            if layout_mode is not None:
                stack_parent, layout, _ = layout_mode
                if layout.indexOf(existing) >= 0:
                    next_layout_index = _ensure_button_in_layout(
                        existing,
                        stack_parent,
                        layout,
                        style_anchor,
                        next_layout_index,
                    )
                    _rewire_button(existing, opener, main_window)
                    existing.show()
                    setattr(main_window, marker, True)
                    changed = True
                    continue
            elif geometry_mode is not None and _button_in_geometry_stack(existing, geometry_mode[0]):
                _rewire_button(existing, opener, main_window)
                existing.show()
                setattr(main_window, marker, True)
                changed = True
                continue
            _destroy_widget(existing)

        if layout_mode is not None:
            stack_parent, layout, _ = layout_mode
            if _insert_into_stack(
                main_window,
                stack_parent,
                layout,
                style_anchor,
                next_layout_index,
                marker,
                text,
                opener,
            ):
                next_layout_index += 1
                changed = True
        elif geometry_mode is not None and next_geometry_y is not None:
            parent, anchor_container, gap = geometry_mode
            button = _insert_geometry_button(
                main_window,
                parent,
                anchor_container,
                next_geometry_y,
                marker,
                text,
                opener,
                style_anchor,
            )
            if button is not None:
                next_geometry_y = button.y() + button.height() + gap
                changed = True

    ready = _buttons_ready_and_aligned(main_window)
    if ready:
        _log("home menu buttons 05/06 ready")
    else:
        _log("home menu buttons 05/06 still missing after install")
    return changed or ready


def _buttons_ready_and_aligned(main_window: QWidget) -> bool:
    for text in (BUTTON_05_TEXT, BUTTON_06_TEXT):
        button = _find_menu_button(main_window, text)
        if button is None or not button.isVisible():
            return False

    layout_stack = _find_menu_button_stack(main_window)
    if layout_stack is not None:
        _, layout, stack_buttons, _ = layout_stack
        stack_numbers = {_subtree_menu_number(button) for button in stack_buttons}
        stack_numbers.discard(None)
        if not {1, 4}.issubset(stack_numbers):
            return False
        for text in (BUTTON_05_TEXT, BUTTON_06_TEXT):
            button = _find_menu_button(main_window, text)
            if button is None or layout.indexOf(button) < 0:
                return False
        return True

    geometry_stack = _find_geometry_stack(main_window)
    if geometry_stack is None:
        return False
    for text in (BUTTON_05_TEXT, BUTTON_06_TEXT):
        button = _find_menu_button(main_window, text)
        if button is None or not _button_in_geometry_stack(button, geometry_stack.parent):
            return False
    return True


def _button_in_geometry_stack(button: QPushButton, parent: QWidget) -> bool:
    return button.parentWidget() == parent and button.y() > 0


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


def _remove_misplaced_geometry_patch_widgets(root: QWidget, parent: QWidget) -> None:
    valid_texts = {
        BUTTON_05_TEXT.replace(" ", ""),
        BUTTON_06_TEXT.replace(" ", ""),
    }
    for widget in _iter_patch_widgets(root):
        if isinstance(widget, QPushButton):
            text = widget.text().replace(" ", "")
            if text in valid_texts and widget.parentWidget() == parent:
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
    for button in root.findChildren(QPushButton):
        text = button.text().replace(" ", "")
        if text in {
            BUTTON_05_TEXT.replace(" ", ""),
            BUTTON_06_TEXT.replace(" ", ""),
            _LEGACY_BUTTON_05_TEXT.replace(" ", ""),
        }:
            widgets.append(button)
    return _unique_widget_list(widgets)


def _destroy_widget(widget: QWidget) -> None:
    parent = widget.parentWidget()
    if parent is not None:
        layout = parent.layout()
        if layout is not None:
            _remove_from_layout(layout, widget)
    widget.hide()
    widget.deleteLater()
    _log(f"removed duplicate patch widget: {_combined_widget_text(widget)}")


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
    _apply_button_style(button, style_anchor)
    _rewire_button(button, opener, main_window)

    if not _insert_button_at(layout, insert_index, button):
        button.deleteLater()
        _log(f"failed stack insert for {text}")
        return False

    button.show()
    button.raise_()
    setattr(main_window, marker, True)
    _log(f"inserted {text} into stack at {insert_index}")
    return True


def _insert_geometry_button(
    main_window: QWidget,
    parent: QWidget,
    anchor_container: QWidget,
    y_pos: int,
    marker: str,
    text: str,
    opener: Callable[[QWidget, QWidget], None],
    style_anchor: QWidget,
) -> Optional[QPushButton]:
    button = QPushButton(text, parent)
    button.setObjectName(marker.lower())
    _apply_button_style(button, style_anchor)
    _rewire_button(button, opener, main_window)

    width = anchor_container.width()
    height = anchor_container.height()
    if width <= 0 or height <= 0:
        width = max(style_anchor.width(), 320)
        height = max(style_anchor.height(), 72)

    button.setGeometry(anchor_container.x(), y_pos, width, height)
    button.show()
    button.raise_()
    setattr(main_window, marker, True)
    _log(f"inserted {text} by geometry at y={y_pos}")
    return button


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


def _layout_item_for_widget(layout: QLayout, widget: QWidget) -> Tuple[Optional[QWidget], int]:
    current: Optional[QWidget] = widget
    while current is not None:
        index = layout.indexOf(current)
        if index >= 0:
            return current, index
        current = current.parentWidget()
    return None, -1


def _extract_menu_number(text: str) -> Optional[int]:
    stripped = text.strip()
    if not stripped:
        return None
    match = _NUMBERED_BUTTON_RE.match(stripped)
    if match:
        return int(match.group(1))
    compact = stripped.replace(" ", "")
    for number, keywords in _MENU_KEYWORDS.items():
        for keyword in keywords:
            if keyword in stripped or keyword in compact:
                return number
    return None


def _combined_widget_text(widget: QWidget) -> str:
    parts: List[str] = []
    own_text = _widget_label_text(widget).strip()
    if own_text:
        parts.append(own_text)
    for child in widget.findChildren(QLabel):
        child_text = child.text().strip()
        if child_text:
            parts.append(child_text)
    for child in widget.findChildren(QAbstractButton):
        child_text = child.text().strip()
        if child_text:
            parts.append(child_text)
    return " ".join(parts)


def _subtree_menu_number(widget: QWidget) -> Optional[int]:
    number = _extract_menu_number(_combined_widget_text(widget))
    if number is not None:
        return number
    for child in widget.findChildren(QWidget):
        number = _extract_menu_number(_combined_widget_text(child))
        if number is not None:
            return number
    return None


def _layout_menu_items(layout: QLayout) -> List[Tuple[int, QWidget, int]]:
    items: List[Tuple[int, QWidget, int]] = []
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None:
            continue
        child = item.widget()
        if child is None:
            continue
        number = _subtree_menu_number(child)
        if number is None or number > 4:
            continue
        items.append((number, child, index))
    return items


def _layout_menu_score(layout: QLayout, menu_items: List[Tuple[int, QWidget, int]]) -> int:
    numbers = {number for number, _, _ in menu_items}
    score = len(numbers) * 10
    if 1 in numbers:
        score += 5
    if 4 in numbers:
        score += 5
    if isinstance(layout, QBoxLayout) and layout.direction() == Qt.Vertical:
        score += 20
    return score


def _group_menu_buttons_by_layout(root: QWidget) -> Dict[QLayout, List[QWidget]]:
    grouped: Dict[QLayout, List[QWidget]] = defaultdict(list)
    for widget in _iter_menu_label_widgets(root):
        number = _extract_menu_number(_combined_widget_text(widget))
        if number is None or number > 4:
            continue
        layout, index = _find_layout_for_widget(widget)
        if layout is None or index < 0:
            continue
        grouped[layout].append(widget)
    return grouped


def _find_menu_button_stack(root: QWidget) -> Optional[LayoutStack]:
    anchor = _find_anchor_button(root)
    if anchor is None:
        return None

    best_layout: Optional[QLayout] = None
    best_items: List[Tuple[int, QWidget, int]] = []
    best_score = -1

    current: Optional[QWidget] = anchor
    while current is not None:
        parent = current.parentWidget()
        if parent is None:
            break
        layout = parent.layout()
        if layout is not None:
            menu_items = _layout_menu_items(layout)
            unique_numbers = {number for number, _, _ in menu_items}
            if len(unique_numbers) >= 2:
                score = _layout_menu_score(layout, menu_items)
                if score > best_score:
                    best_score = score
                    best_layout = layout
                    best_items = menu_items
        current = parent

    if best_layout is None or len(best_items) < 2:
        grouped = _group_menu_buttons_by_layout(root)
        for layout, buttons in grouped.items():
            unique = _unique_buttons_sorted(buttons)
            if len(unique) <= len(best_items):
                continue
            menu_items = []
            for button in unique:
                number = _extract_menu_number(_combined_widget_text(button))
                if number is None:
                    continue
                target, index = _layout_item_for_widget(layout, button)
                if target is not None and index >= 0:
                    menu_items.append((number, target, index))
            if len(menu_items) > len(best_items):
                best_layout = layout
                best_items = menu_items

    if best_layout is None or len(best_items) < 2:
        return None

    menu_items = sorted(best_items, key=lambda item: item[0])
    numbers = [number for number, _, _ in menu_items]
    if 4 not in numbers:
        return None

    stack_buttons = [widget for _, widget, _ in menu_items]
    last_index = max(index for _, _, index in menu_items)
    stack_parent = _layout_owner(best_layout) or stack_buttons[-1].parentWidget()
    if stack_parent is None:
        return None

    _log(
        "home-menu stack found: parent="
        f"{stack_parent.__class__.__name__}, buttons={numbers}, insert_after={last_index}"
    )
    return stack_parent, best_layout, stack_buttons, last_index


def _pick_menu_container(widget: QWidget) -> QWidget:
    current = widget
    best = widget
    while current.parentWidget() is not None:
        parent = current.parentWidget()
        if len(_menu_numbers_in_widget_subtree(parent)) > 1:
            break
        best = current
        current = parent
    return best


def _menu_numbers_in_widget_subtree(widget: QWidget) -> set[int]:
    numbers: set[int] = set()
    for child in widget.findChildren(QWidget):
        number = _extract_menu_number(_combined_widget_text(child))
        if number is not None and 1 <= number <= 4:
            numbers.add(number)
        if len(numbers) >= 4:
            break
    return numbers


def _scan_menu_containers(root: QWidget) -> List[Tuple[int, QWidget]]:
    entries: Dict[int, QWidget] = {}
    for widget in root.findChildren(QWidget):
        combined = _combined_widget_text(widget)
        number = _extract_menu_number(combined)
        if number is None or number > 4:
            continue
        container = _pick_menu_container(widget)
        area = max(container.width(), 1) * max(container.height(), 1)
        previous = entries.get(number)
        if previous is None:
            entries[number] = container
            continue
        previous_area = max(previous.width(), 1) * max(previous.height(), 1)
        if area >= previous_area:
            entries[number] = container
    return sorted(entries.items(), key=lambda item: item[0])


def _find_common_parent(widgets: List[QWidget]) -> Optional[QWidget]:
    if not widgets:
        return None
    parents: List[QWidget] = []
    current: Optional[QWidget] = widgets[0]
    while current is not None:
        parents.append(current)
        current = current.parentWidget()
    for candidate in parents:
        if all(_is_descendant_of(widget, candidate) for widget in widgets):
            return candidate
    return widgets[0].parentWidget()


def _is_descendant_of(widget: QWidget, ancestor: QWidget) -> bool:
    current: Optional[QWidget] = widget
    while current is not None:
        if current is ancestor:
            return True
        current = current.parentWidget()
    return False


def _find_geometry_stack(root: QWidget) -> Optional[GeometryStack]:
    containers = _scan_menu_containers(root)
    if len(containers) < 2 or containers[-1][0] != 4:
        return None

    container_widgets = [widget for _, widget in containers]
    parent = container_widgets[0].parentWidget()
    if parent is None:
        parent = root
    if not all(widget.parentWidget() == parent for widget in container_widgets):
        common_parent = _find_common_parent(container_widgets)
        if common_parent is None:
            return None
        parent = common_parent

    gap = 12
    if len(containers) >= 2:
        prev_widget = containers[-2][1]
        last_widget = containers[-1][1]
        gap = max(12, last_widget.y() - (prev_widget.y() + prev_widget.height()))

    return GeometryStack(parent=parent, containers=containers, gap=gap)


def _find_anchor_button(root: QWidget) -> Optional[QWidget]:
    for widget in root.findChildren(QWidget):
        combined = _combined_widget_text(widget)
        if "光学小实验" in combined:
            return widget
        if _extract_menu_number(combined) == 4:
            return widget
    return None


def _unique_buttons_sorted(buttons: List[QWidget]) -> List[QWidget]:
    seen = set()
    unique: List[QWidget] = []
    for button in sorted(
        buttons,
        key=lambda item: _extract_menu_number(_combined_widget_text(item)) or 99,
    ):
        obj_id = id(button)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        unique.append(button)
    return unique


def _unique_widget_list(widgets: List[QWidget]) -> List[QWidget]:
    seen = set()
    unique: List[QWidget] = []
    for widget in widgets:
        obj_id = id(widget)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        unique.append(widget)
    return unique


def _button_number(widget: QWidget) -> Optional[int]:
    return _extract_menu_number(_widget_label_text(widget))


def _style_source_widget(widget: QWidget) -> QWidget:
    for child in widget.findChildren(QAbstractButton):
        text = _widget_label_text(child)
        if text.strip():
            return child
    for child in widget.findChildren(QAbstractButton):
        return child
    return widget


def _apply_button_style(button: QPushButton, style_anchor: QWidget) -> None:
    _match_button_geometry(style_anchor, button)
    button.setCursor(Qt.PointingHandCursor)
    style = _button_style(style_anchor)
    if style:
        button.setStyleSheet(style)
    else:
        button.setStyleSheet(_fallback_menu_style())


def _match_button_geometry(anchor: QWidget, button: QPushButton) -> None:
    button.setSizePolicy(anchor.sizePolicy())
    button.setMinimumSize(anchor.minimumSize())
    button.setMaximumSize(anchor.maximumSize())
    if anchor.width() > 0 and anchor.height() > 0:
        button.setFixedSize(anchor.size())
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


def _fallback_menu_style() -> str:
    return (
        "QPushButton {"
        "border: none;"
        "border-radius: 24px;"
        "color: white;"
        "font-size: 20px;"
        "font-weight: bold;"
        "padding: 18px;"
        "background-color: qlineargradient("
        "spread:pad, x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #58d68d, stop:1 #1e8449"
        ");"
        "}"
        "QPushButton:hover {"
        "background-color: qlineargradient("
        "spread:pad, x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #7dcea0, stop:1 #239b56"
        ");"
        "}"
    )


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
    for widget in root.findChildren(QWidget):
        combined = _combined_widget_text(widget)
        number = _extract_menu_number(combined)
        if number is None or number > 4:
            continue
        obj_id = id(widget)
        if obj_id in seen:
            continue
        seen.add(obj_id)
        widgets.append(widget)
    return widgets


def _iter_clickable_widgets(root: QWidget) -> List[QWidget]:
    return _iter_menu_label_widgets(root)


def _widget_label_text(widget: QWidget) -> str:
    if isinstance(widget, QAbstractButton):
        return widget.text()
    if isinstance(widget, QLabel):
        return widget.text()
    if hasattr(widget, "text"):
        try:
            value = widget.text()  # type: ignore[attr-defined]
            if isinstance(value, str):
                return value
        except Exception:  # noqa: BLE001
            return ""
    return ""


def _button_style(anchor: QWidget) -> str:
    anchor_style = anchor.styleSheet().strip()
    if anchor_style:
        return anchor_style
    parent = anchor.parentWidget()
    if parent is not None:
        parent_style = parent.styleSheet().strip()
        if parent_style:
            return parent_style
    return ""


def _dump_menu_widgets_once(root: QWidget) -> None:
    global _DUMPED_WIDGETS
    if _DUMPED_WIDGETS:
        return
    _DUMPED_WIDGETS = True
    _log("dumping menu-related widgets for diagnosis")
    for widget in root.findChildren(QWidget):
        combined = _combined_widget_text(widget)
        if not combined:
            continue
        number = _extract_menu_number(combined)
        if number is None and not any(
            keyword in combined for keywords in _MENU_KEYWORDS.values() for keyword in keywords
        ):
            continue
        global_pos: Union[QPoint, str]
        try:
            global_pos = widget.mapToGlobal(QPoint(0, 0))
        except Exception:  # noqa: BLE001
            global_pos = "?"
        _log(
            "widget "
            f"{widget.__class__.__name__}"
            f" name={widget.objectName()!r}"
            f" number={number}"
            f" text={combined!r}"
            f" geom=({widget.x()},{widget.y()},{widget.width()},{widget.height()})"
            f" global={global_pos}"
        )


def _open_ar_imaging_adjustment(main_window: QWidget, _button: QWidget) -> None:
    from app.ar_imaging_adjustment import ARImagingAdjustmentWindow

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
    from app.ai_experiment_llm_judgement import AIExperimentLLMJudgementWindow

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
