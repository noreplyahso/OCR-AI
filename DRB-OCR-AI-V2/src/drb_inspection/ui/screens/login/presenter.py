from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.context import LoginCommand
from drb_inspection.application.use_cases.login_user import LoginUserUseCase
from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.screens.login.state import LoginScreenState, LoginSubmitResult


@dataclass
class LoginScreenPresenter:
    login_user: LoginUserUseCase

    def load(self) -> LoginScreenState:
        return LoginScreenState()

    def submit(self, user_name: str, password: str) -> LoginSubmitResult:
        result = self.login_user.execute(LoginCommand(user_name=user_name, password=password))
        return LoginSubmitResult(
            state=LoginScreenState(
                user_name=user_name,
                password="",
                can_submit=True,
                message=result.message,
            ),
            next_screen=ScreenId.MAIN if result.success else None,
        )
