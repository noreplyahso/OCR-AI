from drb_inspection.adapters.db.models import UserRecord
from drb_inspection.app.container import build_container
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.screens.login.presenter import LoginScreenPresenter
from drb_inspection.ui.screens.main.presenter import MainScreenPresenter
from drb_inspection.ui.shell import DesktopShell


def test_login_presenter_moves_to_main_on_success() -> None:
    container = build_container()
    container.repository.save_user(UserRecord(user_name="operator3", password_hash="pw", role="Operator"))
    presenter = LoginScreenPresenter(login_user=container.login_user)

    result = presenter.submit(user_name="operator3", password="pw")

    assert result.next_screen == ScreenId.MAIN
    assert "success" in result.state.message.lower()


def test_main_presenter_loads_state_from_application_use_cases() -> None:
    container = build_container()
    container.repository.update_session(user_name="admin", product_name="PRODUCT-A")
    presenter = MainScreenPresenter(
        load_main_screen_context=container.load_main_screen_context,
        load_session_settings=container.load_session_settings,
        load_runtime_status=container.load_runtime_status,
        configure_camera=container.configure_camera,
        grab_preview=container.grab_preview,
        save_session_settings=container.save_session_settings,
        select_product=container.select_product,
        run_current_product_cycle=container.run_current_product_cycle,
    )

    state = presenter.load()

    assert state.current_user_name == "admin"
    assert state.current_role == "Administrator"
    assert "PRODUCT-A" in state.available_products
    assert state.model_path == "models/product_a.pt"
    assert state.access_profile.can_run_cycle is True
    assert state.camera_connected is True
    assert state.plc_connected is True


def test_desktop_shell_launches_login_then_transitions_to_main_after_submit() -> None:
    container = build_container()
    container.repository.save_user(UserRecord(user_name="operator4", password_hash="pw", role="Operator"))
    shell = DesktopShell(container=container)

    initial_screen = shell.launch()
    next_screen = shell.submit_login("operator4", "pw")

    assert initial_screen == ScreenId.LOGIN
    assert next_screen == ScreenId.MAIN
    assert shell.main_state is not None
    assert shell.main_state.current_user_name == "operator4"
    assert shell.main_state.selected_product_name == "PRODUCT-A"


def test_desktop_shell_logout_returns_to_login() -> None:
    container = build_container()
    container.repository.save_user(UserRecord(user_name="operator5", password_hash="pw", role="Operator"))
    shell = DesktopShell(container=container)

    shell.launch()
    shell.submit_login("operator5", "pw")
    screen = shell.logout()

    assert screen == ScreenId.LOGIN
    assert shell.main_state is None
    assert shell.login_state is not None


def test_main_presenter_can_run_cycle_for_selected_product() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=True))
    container.repository.update_session(user_name="admin", product_name="PRODUCT-A")
    presenter = MainScreenPresenter(
        load_main_screen_context=container.load_main_screen_context,
        load_session_settings=container.load_session_settings,
        load_runtime_status=container.load_runtime_status,
        configure_camera=container.configure_camera,
        grab_preview=container.grab_preview,
        save_session_settings=container.save_session_settings,
        select_product=container.select_product,
        run_current_product_cycle=container.run_current_product_cycle,
    )

    state = presenter.run_cycle()

    assert state.last_cycle_status == "pass"
    assert "OK" in state.message
    assert state.plc_last_result == "OK"
    assert state.task_summaries


def test_main_presenter_can_grab_preview_frame() -> None:
    container = build_container()
    container.repository.update_session(user_name="admin", product_name="PRODUCT-A")
    presenter = MainScreenPresenter(
        load_main_screen_context=container.load_main_screen_context,
        load_session_settings=container.load_session_settings,
        load_runtime_status=container.load_runtime_status,
        configure_camera=container.configure_camera,
        grab_preview=container.grab_preview,
        save_session_settings=container.save_session_settings,
        select_product=container.select_product,
        run_current_product_cycle=container.run_current_product_cycle,
    )

    state = presenter.grab_preview_frame()

    assert state.preview_frame is not None
    assert "Frame source:" in state.preview_summary
