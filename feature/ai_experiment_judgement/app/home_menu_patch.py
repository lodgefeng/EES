# -*- coding: utf-8 -*-
"""Runtime home-menu patch: add the 05 | AI实验判断 button."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from app.ai_experiment_judgement import AIExperimentJudgementWindow

PATCH_MARKER = "AI_EXPERIMENT_JUDGEMENT_BUTTON_05"
BUTTON_TEXT = "05 | AI实验判断"


def install_ai_experiment_menu_button(main_window: QWidget) -> bool:
    """Insert button 05 below the existing optics experiment button."""
    if getattr(main_window, PATCH_MARKER, False):
        return True

    anchor = _find_anchor_button(main_window)
    if anchor is None:
        return False

    parent = anchor.parentWidget()
    if parent is None:
        return False

    layout = parent.layout()
    if not isinstance(layout, QVBoxLayout):
        return False

    index = layout.indexOf(anchor)
    if index < 0:
        return False

    button = QPushButton(BUTTON_TEXT, parent)
    button.setObjectName("btn_ai_experiment_judgement")
    button.setMinimumHeight(max(anchor.minimumHeight(), 72))
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(_button_style(anchor))
    button.clicked.connect(lambda: _open_ai_experiment_judgement(main_window))

    layout.insertWidget(index + 1, button)
    setattr(main_window, PATCH_MARKER, True)
    return True


def schedule_ai_experiment_menu_button(main_window: QWidget) -> None:
    """Run after the home page layout is ready."""
    from PySide6.QtCore import QTimer

    def _try_install() -> None:
        if install_ai_experiment_menu_button(main_window):
            return
        QTimer.singleShot(200, _try_install)

    QTimer.singleShot(0, _try_install)


def install_on_top_level_window() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    for widget in app.topLevelWidgets():
        if widget.isVisible() and install_ai_experiment_menu_button(widget):
            return True
    return False


def _find_anchor_button(root: QWidget) -> Optional[QPushButton]:
    candidates = []
    for button in root.findChildren(QPushButton):
        text = button.text().replace(" ", "")
        if "光学小实验" in text or text.startswith("04|"):
            candidates.append(button)
    if not candidates:
        for button in root.findChildren(QPushButton):
            if button.text().strip().startswith("04"):
                candidates.append(button)
    if not candidates:
        return None
    return max(candidates, key=lambda btn: len(btn.text()))


def _button_style(anchor: QPushButton) -> str:
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
