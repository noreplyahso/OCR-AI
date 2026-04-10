from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.shell import DesktopShell


class LoginScreenWidget(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, shell: DesktopShell):
        super().__init__()
        self.shell = shell
        self.card = QFrame()
        self.card.setObjectName("card")
        self.message_label = QLabel("")
        self.message_label.setObjectName("messageLabel")
        self.user_name_edit = QLineEdit()
        self.user_name_edit.setPlaceholderText("admin")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("admin")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("primaryButton")
        self.login_button.clicked.connect(self._on_submit)
        self._build_ui()

    def render(self) -> None:
        state = self.shell.login_state or self.shell.login_presenter.load()
        self.user_name_edit.setText(state.user_name)
        self.password_edit.setText("")
        self.message_label.setText(state.message)
        self.login_button.setEnabled(state.can_submit)

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(36, 36, 36, 36)
        title = QLabel("DRB OCR AI V2")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Sign in to continue with the current local demo container.")
        subtitle.setObjectName("screenSubtitle")

        hint_label = QLabel("Default demo account: admin / admin")
        hint_label.setObjectName("mutedLabel")

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft)
        form.addRow("User name", self.user_name_edit)
        form.addRow("Password", self.password_edit)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(4)
        card_layout.addWidget(hint_label)
        card_layout.addSpacing(6)
        card_layout.addLayout(form)
        card_layout.addWidget(self.message_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_button)
        self.card.setLayout(card_layout)
        self.card.setMaximumWidth(560)

        center = QHBoxLayout()
        center.addStretch(1)
        center.addWidget(self.card)
        center.addStretch(1)

        layout.addStretch(1)
        layout.addLayout(center)
        layout.addStretch(2)
        self.setLayout(layout)

    def _on_submit(self) -> None:
        next_screen = self.shell.submit_login(
            self.user_name_edit.text(),
            self.password_edit.text(),
        )
        self.render()
        if next_screen == ScreenId.MAIN:
            self.navigate.emit(ScreenId.MAIN.value)
