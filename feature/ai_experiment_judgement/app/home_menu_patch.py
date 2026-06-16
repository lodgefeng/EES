# -*- coding: utf-8 -*-
"""Add home menu buttons 05/06 to Creolight."""

from __future__ import annotations

import os
import re
import traceback
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

BUTTON_05_TEXT = "05 | AR成像调节"
BUTTON_06_TEXT = "06 | AI实验判断"
_NUMBERED_BUTTON = re.compile(r"^(\d{2})\s*\|")
_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Creolight",
    "AR_Camera_Ollama",
    "home_menu_patch.log",
)
_RUNTIME_HOOKED = False


def activate_menu_patch_runtime() -> None:
    global _RUNTIME_HOOKED
    if _RUNTIME_HOOKED:
        return

    original_init = QApplication.__init__

    def patched_init(app_self, *args, **kwargs):
        original_init(app_self, *args, **kwargs)
        app_self.installEventFilter(_MenuPatchEventFilter(app_self))
        for delay_ms in (0, 100, 300, 800, 1500, 3000, 6000, 12000):
            QTimer.singleShot(delay_ms, _ensure_menu_buttons)

    QApplication.__init__ = patched_init  # type: ignore[method-assign]
    _RUNTIME_HOOKED = True
    _log(f"menu patch active: {__file__}")
    QTimer.singleShot(0, _ensure_menu_buttons)


class _MenuPatchEventFilter(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self._app = app

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Show, QEvent.Polish):
            QTimer.singleShot(0, _ensure_menu_buttons)
        return super().eventFilter(watched, event)


def _ensure_menu_buttons() -> None:
    app = QApplication.instance()
    if app is None:
        return

    if _buttons_ready(app):
        return

    home = _find_home_window(app)
    if home is not None and _inject_into_main_menu(home):
        _log("injected buttons 05/06 into main menu")
        return

    if _show_extension_window(home):
        _log("extension window shown with buttons 05/06")


def _buttons_ready(app: QApplication) -> bool:
    return (
        _find_button_globally(app, BUTTON_05_TEXT) is not None
        and _find_button_globally(app, BUTTON_06_TEXT) is not None
    )


def _find_button_globally(app: QApplication, text: str) -> Optional[QPushButton]:
    compact = text.replace(" ", "")
    for button in app.allWidgets():
        if isinstance(button, QPushButton) and button.text().replace(" ", "") == compact:
            return button
    return None


def _find_home_window(app: QApplication) -> Optional[QWidget]:
    numbered: List[Tuple[int, QPushButton]] = []
    for button in app.allWidgets():
        if not isinstance(button, QPushButton):
            continue
        match = _NUMBERED_BUTTON.match(button.text().strip())
        if match:
            numbered.append((int(match.group(1)), button))

    if numbered:
        _, anchor = max(numbered, key=lambda item: item[0])
        window = anchor.window()
        if window is not None:
            return window

    best: Optional[QWidget] = None
    best_score = -1
    for widget in app.topLevelWidgets():
        if not widget.isVisible():
            continue
        title = widget.windowTitle() or ""
        score = 0
        if widget.isWindow():
            score += 10
        if any(token in title for token in ("光创元", "Creolight", "AR", "教学")):
            score += 100
        if widget.width() >= 600:
            score += 20
        if score > best_score:
            best_score = score
            best = widget
    return best


def _collect_numbered_buttons(root: QWidget) -> List[Tuple[int, QPushButton]]:
    found: List[Tuple[int, QPushButton]] = []
    for button in root.findChildren(QPushButton):
        match = _NUMBERED_BUTTON.match(button.text().strip())
        if match:
            found.append((int(match.group(1)), button))
    found.sort(key=lambda item: item[0])
    return found


def _inject_into_main_menu(home: QWidget) -> bool:
    numbered = _collect_numbered_buttons(home)
    if not numbered:
        _log("no numbered home-menu buttons found")
        return False

    if _find_button(home, BUTTON_05_TEXT) and _find_button(home, BUTTON_06_TEXT):
        return True

    _, anchor = numbered[-1]
    parent = anchor.parentWidget()
    if parent is None:
        _log("numbered button has no parent widget")
        return False

    if _find_button(parent, BUTTON_05_TEXT) or _find_button(parent, BUTTON_06_TEXT):
        return True

    layout = parent.layout()
    if layout is not None:
        return _inject_with_layout(parent, layout, anchor)

    return _inject_with_geometry(parent, anchor)


def _inject_with_layout(parent: QWidget, layout: QLayout, anchor: QPushButton) -> bool:
    index = layout.indexOf(anchor)
    if index < 0:
        _log(f"layout does not contain anchor button: {anchor.text()}")
        return False

    style = anchor.styleSheet()
    height = max(anchor.minimumHeight(), anchor.height(), 68)

    button_05 = _make_menu_button(BUTTON_05_TEXT, _open_button_05, style, height, parent)
    button_06 = _make_menu_button(BUTTON_06_TEXT, _open_button_06, style, height, parent)

    if isinstance(layout, QVBoxLayout):
        layout.insertWidget(index + 1, button_05)
        layout.insertWidget(index + 2, button_06)
        return True

    if isinstance(layout, QGridLayout):
        row, column, row_span, column_span = layout.getItemPosition(index)
        layout.addWidget(button_05, row + row_span, column, row_span, column_span)
        layout.addWidget(button_06, row + row_span * 2, column, row_span, column_span)
        return True

    _log(f"unsupported layout type: {type(layout).__name__}")
    return False


def _inject_with_geometry(parent: QWidget, anchor: QPushButton) -> bool:
    if _find_button(parent, BUTTON_05_TEXT) or _find_button(parent, BUTTON_06_TEXT):
        return True

    style = anchor.styleSheet()
    height = max(anchor.minimumHeight(), anchor.height(), 68)
    gap = 12
    anchor_rect = anchor.geometry()

    button_05 = _make_menu_button(BUTTON_05_TEXT, _open_button_05, style, height, parent)
    button_06 = _make_menu_button(BUTTON_06_TEXT, _open_button_06, style, height, parent)

    button_05.setGeometry(
        anchor_rect.x(),
        anchor_rect.y() + anchor_rect.height() + gap,
        anchor_rect.width(),
        height,
    )
    button_06.setGeometry(
        anchor_rect.x(),
        anchor_rect.y() + anchor_rect.height() + gap + height + gap,
        anchor_rect.width(),
        height,
    )
    button_05.show()
    button_06.show()
    return True


def _make_menu_button(
    text: str,
    opener: Callable[[], None],
    style: str,
    height: int,
    parent: QWidget,
) -> QPushButton:
    button = QPushButton(text, parent)
    button.setMinimumHeight(height)
    button.setCursor(Qt.PointingHandCursor)
    if style:
        button.setStyleSheet(style)
    else:
        button.setStyleSheet(_default_button_style(text))
    button.clicked.connect(opener)
    button.show()
    button.raise_()
    return button


def _show_extension_window(home: Optional[QWidget]) -> bool:
    app = QApplication.instance()
    if app is None:
        return False

    win: Optional[QWidget] = getattr(app, "_creolight_menu_extension_win", None)
    if win is None:
        win = QWidget(None, Qt.Window | Qt.WindowStaysOnTopHint | Qt.Tool)
        win.setObjectName("creolight_menu_extension_win")
        win.setWindowTitle("扩展功能 05 / 06")
        win.setAttribute(Qt.WA_QuitOnClose, False)
        layout = QVBoxLayout(win)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(_make_menu_button(BUTTON_05_TEXT, _open_button_05, _button_style_05(), 68, win))
        layout.addWidget(_make_menu_button(BUTTON_06_TEXT, _open_button_06, _button_style_06(), 68, win))
        setattr(app, "_creolight_menu_extension_win", win)

    _position_extension_window(home, win)
    win.show()
    win.raise_()
    win.activateWindow()
    return True


def _position_extension_window(home: Optional[QWidget], win: QWidget) -> None:
    if home is not None and home.isVisible():
        geo = home.frameGeometry()
        width = max(int(geo.width() * 0.42), 380)
        height = 190
        x = geo.x() + int(geo.width() * 0.29)
        y = geo.y() + int(geo.height() * 0.52)
        win.setGeometry(x, y, width, height)
        return

    screen = QApplication.primaryScreen()
    if screen is None:
        win.resize(400, 200)
        return
    geo = screen.availableGeometry()
    width = 400
    height = 200
    x = geo.x() + (geo.width() - width) // 2
    y = geo.y() + int(geo.height() * 0.55)
    win.setGeometry(x, y, width, height)


def _find_button(parent: QWidget, text: str) -> Optional[QPushButton]:
    compact = text.replace(" ", "")
    for button in parent.findChildren(QPushButton):
        if button.text().replace(" ", "") == compact:
            return button
    return None


def _default_button_style(text: str) -> str:
    if text.startswith("05"):
        return _button_style_05()
    return _button_style_06()


def _button_style_05() -> str:
    return (
        "QPushButton { border:none; border-radius:24px; color:white; font-size:20px; font-weight:bold;"
        "background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #5dade2, stop:1 #2e86c1); }"
        "QPushButton:hover { background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7fb3e8, stop:1 #3498db); }"
    )


def _button_style_06() -> str:
    return (
        "QPushButton { border:none; border-radius:24px; color:white; font-size:20px; font-weight:bold;"
        "background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #58d68d, stop:1 #1e8449); }"
        "QPushButton:hover { background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7dcea0, stop:1 #239b56); }"
    )


def _open_button_05() -> None:
    from app.ar_imaging_adjustment import ARImagingAdjustmentWindow

    app = QApplication.instance()
    home = _find_home_window(app) if app is not None else None
    window = ARImagingAdjustmentWindow(home_window=home)
    window.resize(1280, 860)
    if home is not None:
        home.hide()
    window.show()


def _open_button_06() -> None:
    from app.ai_experiment_llm_judgement import AIExperimentLLMJudgementWindow

    app = QApplication.instance()
    home = _find_home_window(app) if app is not None else None
    window = AIExperimentLLMJudgementWindow(home_window=home)
    window.resize(1180, 900)
    if home is not None:
        home.hide()
    window.show()


def _log(message: str) -> None:
    if not _LOG_PATH:
        return
    try:
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


install_home_menu_buttons = _ensure_menu_buttons
install_on_top_level_window = _ensure_menu_buttons
schedule_ai_experiment_menu_button = lambda window: QTimer.singleShot(0, _ensure_menu_buttons)
