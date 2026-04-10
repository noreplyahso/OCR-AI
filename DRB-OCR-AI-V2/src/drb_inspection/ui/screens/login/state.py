from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.ui.navigation import ScreenId


@dataclass(frozen=True)
class LoginScreenState:
    title: str = "Login"
    user_name: str = ""
    password: str = ""
    can_submit: bool = True
    message: str = ""


@dataclass(frozen=True)
class LoginSubmitResult:
    state: LoginScreenState
    next_screen: ScreenId | None = None
