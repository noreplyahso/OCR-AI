from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

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
            connect_camera=self.container.connect_camera,
            disconnect_camera=self.container.disconnect_camera,
            connect_plc=self.container.connect_plc,
            disconnect_plc=self.container.disconnect_plc,
            shutdown_runtime=self.container.shutdown_runtime,
            configure_camera=self.container.configure_camera,
            grab_preview=self.container.grab_preview,
            import_product_catalog=self.container.import_product_catalog,
            save_session_settings=self.container.save_session_settings,
            move_session_roi=self.container.move_session_roi,
            save_product_settings=self.container.save_product_settings,
            select_product=self.container.select_product,
            run_current_product_cycle=self.container.run_current_product_cycle,
            poll_plc_signals=self.container.poll_plc_signals,
        )
        self.main_presenter.runtime_controls.recording_enabled = (
            self.container.run_current_product_cycle.runtime_settings.record_results_default
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
        self.main_presenter.clear_cycle_metrics()
        self.main_presenter.clear_runtime_controls()
        self.login_state = self.login_presenter.load()
        self.main_state = None
        self.active_screen = ScreenId.LOGIN
        return self.active_screen

    def refresh_main(self) -> MainScreenState:
        self.main_state = self.main_presenter.load()
        self.active_screen = ScreenId.MAIN
        return self.main_state

    def open_external_path(self, path: str) -> tuple[bool, str]:
        resolved = str(path or "").strip()
        if not resolved:
            return False, "Artifact path is not available."

        target = Path(resolved)
        if not target.exists():
            return False, f"Artifact path does not exist: {target}"

        try:
            os.startfile(str(target))
        except Exception as exc:
            return False, f"Failed to open artifact path: {exc}"
        return True, f"Opened artifact path: {target}"

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
