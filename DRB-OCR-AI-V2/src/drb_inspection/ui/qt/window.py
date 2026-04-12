from __future__ import annotations

from PyQt5.QtWidgets import QStackedWidget

from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.qt.login_widget import LoginScreenWidget
from drb_inspection.ui.qt.main_widget import MainScreenWidget
from drb_inspection.ui.shell import DesktopShell


class DesktopStackedWindow(QStackedWidget):
    def __init__(self, shell: DesktopShell):
        super().__init__()
        self.shell = shell
        self.setObjectName("desktopWindow")
        self.login_widget = LoginScreenWidget(shell=shell)
        self.main_widget = MainScreenWidget(shell=shell)
        self.addWidget(self.login_widget)
        self.addWidget(self.main_widget)
        self.login_widget.navigate.connect(self.navigate)
        self.main_widget.navigate.connect(self.navigate)
        self.setWindowTitle("DRB OCR AI V2")
        self.resize(1280, 1024)
        self.setMinimumSize(1280, 1024)

    def start(self) -> None:
        screen = self.shell.launch()
        self._apply_screen(screen)
        self.show()

    def navigate(self, screen_name: str) -> None:
        self._apply_screen(ScreenId(screen_name))

    def _apply_screen(self, screen: ScreenId) -> None:
        if screen == ScreenId.MAIN:
            self.main_widget.render()
            self.setCurrentWidget(self.main_widget)
            return
        self.login_widget.render()
        self.setCurrentWidget(self.login_widget)
