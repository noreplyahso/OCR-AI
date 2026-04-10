from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.app.container import AppContainer
from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.screens.login.presenter import LoginScreenPresenter
from drb_inspection.ui.screens.login.state import LoginScreenState
from drb_inspection.ui.screens.main.presenter import MainScreenPresenter
from drb_inspection.ui.screens.main.state import MainScreenState


@dataclass
class DesktopShell:
    """Thin shell. In the real app this will host PyQt screens only."""

    container: AppContainer
    active_screen: ScreenId = ScreenId.LOGIN
    login_state: LoginScreenState | None = None
    main_state: MainScreenState | None = None
    login_presenter: LoginScreenPresenter = field(init=False)
    main_presenter: MainScreenPresenter = field(init=False)

    def __post_init__(self) -> None:
        self.login_presenter = LoginScreenPresenter(login_user=self.container.login_user)
        self.main_presenter = MainScreenPresenter(
            load_main_screen_context=self.container.load_main_screen_context,
            load_session_settings=self.container.load_session_settings,
            load_runtime_status=self.container.load_runtime_status,
            configure_camera=self.container.configure_camera,
            grab_preview=self.container.grab_preview,
            save_session_settings=self.container.save_session_settings,
            select_product=self.container.select_product,
            run_current_product_cycle=self.container.run_current_product_cycle,
        )

    def launch(self) -> ScreenId:
        context = self.container.load_main_screen_context.execute()
        if context.current_user_name:
            self.active_screen = ScreenId.MAIN
            self.main_state = self.main_presenter.load()
        else:
            self.active_screen = ScreenId.LOGIN
            self.login_state = self.login_presenter.load()
        return self.active_screen

    def submit_login(self, user_name: str, password: str) -> ScreenId:
        submit_result = self.login_presenter.submit(user_name=user_name, password=password)
        self.login_state = submit_result.state
        if submit_result.next_screen == ScreenId.MAIN:
            self.active_screen = ScreenId.MAIN
            self.main_state = self.main_presenter.load()
            if self.container.run_current_product_cycle.runtime_settings.auto_preview_on_start:
                self.main_state = self.main_presenter.grab_preview_frame()
        else:
            self.active_screen = ScreenId.LOGIN
        return self.active_screen

    def logout(self) -> ScreenId:
        self.container.logout_user.execute()
        self.login_state = self.login_presenter.load()
        self.main_state = None
        self.active_screen = ScreenId.LOGIN
        return self.active_screen

    def refresh_main(self) -> MainScreenState:
        self.main_state = self.main_presenter.load()
        self.active_screen = ScreenId.MAIN
        return self.main_state

    def show(self) -> None:
        screen = self.launch()
        print("DesktopShell ready")
        if screen == ScreenId.LOGIN and self.login_state is not None:
            print("Active screen: login")
            print(f"Login message: {self.login_state.message or '<empty>'}")
        elif screen == ScreenId.MAIN and self.main_state is not None:
            print(
                "Main screen context:"
                f" user={self.main_state.current_user_name or '<none>'}"
                f" role={self.main_state.current_role}"
                f" products={len(self.main_state.available_products)}"
            )
        print("Next step: wire PyQt screens to application use cases.")
