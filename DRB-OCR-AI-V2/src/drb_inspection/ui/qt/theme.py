from __future__ import annotations

from PyQt5.QtWidgets import QApplication


APP_STYLESHEET = """
QStackedWidget#desktopWindow {
    background-color: #e7edec;
}
"""


def apply_app_theme(app: QApplication) -> None:
    app.setStyleSheet(APP_STYLESHEET)
