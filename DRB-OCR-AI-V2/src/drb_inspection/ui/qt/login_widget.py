from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QDateTime, QTimer, pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QMainWindow, QMessageBox
from PyQt5.uic import loadUi

from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.shell import DesktopShell


class LoginScreenWidget(QMainWindow):
    navigate = pyqtSignal(str)

    def __init__(self, shell: DesktopShell):
        super().__init__()
        self.shell = shell
        loadUi(str(self._asset_path("form_UI", "screenLogin.ui")), self)

        self.user_name_edit = self.lineedit_username
        self.password_edit = self.lineedit_password
        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self._update_clock)

        self.user_name_edit.returnPressed.connect(self._on_return_pressed)
        self.password_edit.returnPressed.connect(self._on_return_pressed)
        self.button_login.clicked.connect(self._on_submit)
        self.button_show_password.clicked.connect(self._toggle_password_visibility)

        self.password_edit.setEchoMode(QLineEdit.Password)
        self._update_clock()
        self.clock_timer.start()

    def render(self) -> None:
        state = self.shell.login_state or self.shell.login_presenter.load()
        self.user_name_edit.setText(state.user_name)
        self.password_edit.setText("")
        self.button_login.setEnabled(state.can_submit)

    def _on_submit(self) -> None:
        next_screen = self.shell.submit_login(
            self.user_name_edit.text(),
            self.password_edit.text(),
        )
        state = self.shell.login_state or self.shell.login_presenter.load()
        if next_screen == ScreenId.MAIN:
            self.navigate.emit(ScreenId.MAIN.value)
            return
        if state.message:
            QMessageBox.warning(self, "Login Failed", state.message)
        self.render()

    def _on_return_pressed(self) -> None:
        if not self.user_name_edit.text().strip():
            self.user_name_edit.setFocus()
            return
        if not self.password_edit.text().strip():
            self.password_edit.setFocus()
            return
        self._on_submit()

    def _toggle_password_visibility(self, checked: bool = False) -> None:
        del checked
        current_mode = self.password_edit.echoMode()
        self.password_edit.setEchoMode(
            QLineEdit.Normal if current_mode == QLineEdit.Password else QLineEdit.Password
        )

    def _update_clock(self) -> None:
        self.label_clock.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy  HH:mm:ss"))

    def _asset_path(self, *parts: str) -> Path:
        return Path(__file__).resolve().parents[5].joinpath(*parts)
