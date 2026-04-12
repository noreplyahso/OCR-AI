import os
from dataclasses import replace
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from drb_inspection.adapters.db.models import ProductRecord, UserRecord
from drb_inspection.app.container import build_container
from drb_inspection.application.contracts.context import AccessProfile
from drb_inspection.ui.qt.main_widget import MainScreenWidget
from drb_inspection.ui.shell import DesktopShell
from drb_inspection.ui.screens.main.state import MainScreenState


def _state(**updates) -> MainScreenState:
    return replace(
        MainScreenState(
            selected_product_name="PRODUCT-A",
            camera_connected=True,
            plc_connected=True,
            access_profile=AccessProfile(
                can_run_cycle=True,
                can_manual_mode=True,
                can_auto_mode=True,
                can_live_camera=True,
                can_grab=True,
                can_configure_hardware=True,
            ),
        ),
        **updates,
    )


def _app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def _widget() -> MainScreenWidget:
    app = _app()
    container = build_container()
    container.repository.save_user(UserRecord(user_name="admin", password_hash="admin", role="Administrator"))
    container.repository.upsert_product(
        ProductRecord(product_name="PRODUCT-A", model_path="models/product_a.pt")
    )
    container.repository.update_session(user_name="admin", product_name="PRODUCT-A")
    shell = DesktopShell(container=container)
    shell.launch()
    shell.submit_login("admin", "admin")
    widget = MainScreenWidget(shell=shell)
    widget.show()
    widget.render()
    app.processEvents()
    return widget


def test_cycle_status_visual_state_prefers_hold_state() -> None:
    text, variant = MainScreenWidget._cycle_status_visual_state(
        last_result_label="OK",
        last_cycle_status="pass",
        hold_active=True,
    )

    assert text == "RESULT HOLD"
    assert variant == "hold"


def test_cycle_status_visual_state_maps_operator_result_language() -> None:
    assert MainScreenWidget._cycle_status_visual_state(
        last_result_label="OK",
        last_cycle_status="pass",
        hold_active=False,
    ) == ("OK", "ok")
    assert MainScreenWidget._cycle_status_visual_state(
        last_result_label="FAIL",
        last_cycle_status="fail",
        hold_active=False,
    ) == ("FAIL", "fail")
    assert MainScreenWidget._cycle_status_visual_state(
        last_result_label="Checking",
        last_cycle_status="pass",
        hold_active=False,
    ) == ("CHECKING", "checking")
    assert MainScreenWidget._cycle_status_visual_state(
        last_result_label="",
        last_cycle_status="",
        hold_active=False,
    ) == ("NO CYCLE", "idle")


def test_live_preview_visual_state_matches_v1_language() -> None:
    assert MainScreenWidget._live_preview_visual_state(
        live_active=False,
        hold_active=False,
    ) == ("Live Camera", "inactive")
    assert MainScreenWidget._live_preview_visual_state(
        live_active=True,
        hold_active=False,
    ) == ("Live ON", "active")
    assert MainScreenWidget._live_preview_visual_state(
        live_active=True,
        hold_active=True,
    ) == ("Result Hold", "warning")


def test_control_enabled_map_disables_manual_cycle_in_auto_mode() -> None:
    control_state = MainScreenWidget._control_enabled_map(
        state=_state(auto_mode_enabled=True),
        live_active=False,
        hold_active=False,
    )

    assert control_state["run_cycle"] is False
    assert control_state["auto_mode"] is False
    assert control_state["manual_mode"] is True


def test_control_enabled_map_disables_camera_disconnect_while_live_preview_active() -> None:
    control_state = MainScreenWidget._control_enabled_map(
        state=_state(),
        live_active=True,
        hold_active=False,
    )

    assert control_state["disconnect_camera"] is False


def test_control_enabled_map_disables_manual_cycle_during_result_hold() -> None:
    control_state = MainScreenWidget._control_enabled_map(
        state=_state(auto_mode_enabled=False),
        live_active=True,
        hold_active=True,
    )

    assert control_state["run_cycle"] is False


def test_merge_plc_connect_workflow_state_enables_auto_mode_message() -> None:
    connected_state = _state(message="PLC connected.")
    auto_state = _state(auto_mode_enabled=True, message="Auto mode enabled. PLC polling started.")

    merged = MainScreenWidget._merge_plc_connect_workflow_state(
        connected_state=connected_state,
        auto_state=auto_state,
    )

    assert merged.auto_mode_enabled is True
    assert merged.message == "PLC connected. Auto mode enabled."


def test_merge_plc_disconnect_workflow_state_forces_manual_mode_message() -> None:
    disconnected_state = _state(plc_connected=False, plc_last_result="OK", message="PLC disconnected.")
    manual_state = _state(auto_mode_enabled=False, message="Manual mode enabled.")

    merged = MainScreenWidget._merge_plc_disconnect_workflow_state(
        disconnected_state=disconnected_state,
        manual_state=manual_state,
    )

    assert merged.auto_mode_enabled is False
    assert merged.plc_connected is False
    assert merged.plc_last_result == "OK"
    assert merged.message == "PLC disconnected. Manual mode enabled."


def test_plc_protocol_display_mapping_matches_v1_terms() -> None:
    assert MainScreenWidget._display_plc_protocol("modbus_tcp") == "TCP"
    assert MainScreenWidget._display_plc_protocol("modbus_rtu") == "RTU"
    assert MainScreenWidget._display_plc_protocol("slmp") == "SLMP"
    assert MainScreenWidget._display_plc_protocol("TCP") == "TCP"
    assert MainScreenWidget._display_plc_protocol("RTU") == "RTU"
    assert MainScreenWidget._display_plc_protocol("SLMP") == "SLMP"


def test_plc_protocol_internal_mapping_matches_v2_storage() -> None:
    assert MainScreenWidget._internal_plc_protocol("TCP") == "modbus_tcp"
    assert MainScreenWidget._internal_plc_protocol("RTU") == "modbus_rtu"
    assert MainScreenWidget._internal_plc_protocol("SLMP") == "slmp"
    assert MainScreenWidget._internal_plc_protocol("modbus_tcp") == "modbus_tcp"
    assert MainScreenWidget._internal_plc_protocol("modbus_rtu") == "modbus_rtu"
    assert MainScreenWidget._internal_plc_protocol("slmp") == "slmp"


def test_current_product_updates_collects_widget_values() -> None:
    app = _app()
    widget = _widget()

    widget.combobox_product.setCurrentText("PRODUCT-A")
    widget.current_model_path.setText("models/custom.pt")
    widget.spinbox_default_value.setValue(321)
    widget.spinbox_exposure_time.setValue(4567)
    widget.combobox_acceptance_threshold.setCurrentText("0.65")
    widget.combobox_mns_threshold.setCurrentText("0.35")
    app.processEvents()

    updates = widget._current_product_updates()

    assert updates == {
        "product_name": "PRODUCT-A",
        "model_path": "models/custom.pt",
        "default_number": 321,
        "exposure": 4567,
        "threshold_accept": 0.65,
        "threshold_mns": 0.35,
    }
    widget.clock_timer.stop()
    widget.close()


def test_current_camera_session_updates_collects_widget_values() -> None:
    app = _app()
    widget = _widget()

    widget.spinbox_offset_x.setValue(10)
    widget.spinbox_offset_y.setValue(20)
    widget.spinbox_image_width.setValue(1280)
    widget.spinbox_image_height.setValue(720)
    widget.combobox_zoom_factor.setCurrentText("0.75")
    app.processEvents()

    updates = widget._current_camera_session_updates()

    assert updates == {
        "offset_x": 10,
        "offset_y": 20,
        "image_width": 1280,
        "image_height": 720,
        "zoom_factor": 0.75,
    }
    widget.clock_timer.stop()
    widget.close()


def test_current_plc_session_updates_normalizes_protocol_value() -> None:
    app = _app()
    widget = _widget()

    widget.line_edit_PLCIP.setText("192.168.3.250")
    widget.lineEdit_PLC_port.setText("502")
    widget.comboBox_PLC_protocol.setCurrentText("TCP")
    app.processEvents()

    updates = widget._current_plc_session_updates()

    assert updates == {
        "plc_ip": "192.168.3.250",
        "plc_port": "502",
        "plc_protocol": "modbus_tcp",
    }
    widget.clock_timer.stop()
    widget.close()


def test_open_training_screen_handles_missing_executable_safely(monkeypatch) -> None:
    app = _app()
    widget = _widget()
    dialogs: list[tuple[str, str]] = []

    monkeypatch.setattr(widget, "_resolve_training_executable", lambda: None)
    monkeypatch.setattr(
        "drb_inspection.ui.qt.main_widget.QMessageBox.information",
        lambda _parent, title, message: dialogs.append((title, message)),
    )

    widget._on_open_training_screen()
    app.processEvents()

    assert widget.shell.main_state is not None
    assert "Training tool executable was not found." in widget.shell.main_state.message
    assert dialogs
    widget.clock_timer.stop()
    widget.close()


def test_open_training_screen_stops_live_and_switches_manual_before_launch(monkeypatch, tmp_path) -> None:
    app = _app()
    widget = _widget()
    launched: list[Path] = []
    fake_executable = tmp_path / "OCR_DeepLearning_Software.exe"
    fake_executable.write_text("exe", encoding="utf-8")

    widget.shell.main_state = replace(widget.shell.main_state, auto_mode_enabled=True)
    widget.live_timer.start()

    monkeypatch.setattr(widget, "_resolve_training_executable", lambda: fake_executable)
    monkeypatch.setattr(widget, "_start_training_process", lambda path: launched.append(path))

    widget._on_open_training_screen()
    app.processEvents()

    assert widget.live_timer.isActive() is False
    assert widget.shell.main_state is not None
    assert widget.shell.main_state.auto_mode_enabled is False
    assert launched == [fake_executable]
    widget.clock_timer.stop()
    widget.close()
