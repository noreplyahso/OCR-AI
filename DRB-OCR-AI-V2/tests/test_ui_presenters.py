from datetime import datetime
import os
from pathlib import Path

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.adapters.db.models import InspectionHistoryRecord, ProductRecord, UserRecord
from drb_inspection.adapters.plc.models import PlcReadState
from drb_inspection.app.container import build_container
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.contracts.inspection import (
    InspectionCycleResult,
    InspectionRunResult,
    InspectionTaskResult,
    InspectionTaskType,
    TaskStatus,
)
from drb_inspection.ui.navigation import ScreenId
from drb_inspection.ui.screens.login.presenter import LoginScreenPresenter
from drb_inspection.ui.screens.main.presenter import MainScreenPresenter
from drb_inspection.ui.shell import DesktopShell


def _seed_main_screen_state(container) -> None:
    container.repository.save_user(UserRecord(user_name="admin", password_hash="admin", role="Administrator"))
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-A",
            model_path="models/product_a.pt",
            default_number=160,
            exposure=3500,
            threshold_accept=0.5,
            threshold_mns=0.5,
        )
    )
    container.repository.update_session(user_name="admin", product_name="PRODUCT-A")


def _build_main_presenter(container) -> MainScreenPresenter:
    return MainScreenPresenter(
        load_main_screen_context=container.load_main_screen_context,
        load_session_settings=container.load_session_settings,
        load_runtime_status=container.load_runtime_status,
        connect_camera=container.connect_camera,
        disconnect_camera=container.disconnect_camera,
        connect_plc=container.connect_plc,
        disconnect_plc=container.disconnect_plc,
        shutdown_runtime=container.shutdown_runtime,
        configure_camera=container.configure_camera,
        grab_preview=container.grab_preview,
        import_product_catalog=container.import_product_catalog,
        save_session_settings=container.save_session_settings,
        move_session_roi=container.move_session_roi,
        save_product_settings=container.save_product_settings,
        select_product=container.select_product,
        run_current_product_cycle=container.run_current_product_cycle,
        poll_plc_signals=container.poll_plc_signals,
    )


def test_login_presenter_moves_to_main_on_success() -> None:
    container = build_container()
    container.repository.save_user(UserRecord(user_name="operator3", password_hash="pw", role="Operator"))
    presenter = LoginScreenPresenter(login_user=container.login_user)

    result = presenter.submit(user_name="operator3", password="pw")

    assert result.next_screen == ScreenId.MAIN
    assert "success" in result.state.message.lower()


def test_main_presenter_loads_state_from_application_use_cases() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.load()

    assert state.current_user_name == "admin"
    assert state.current_role == "Administrator"
    assert "PRODUCT-A" in state.available_products
    assert state.model_path == "models/product_a.pt"
    assert state.default_number == 160
    assert state.exposure == 3500
    assert state.threshold_accept == 0.5
    assert state.threshold_mns == 0.5
    assert "ROIs: 5 zones" in state.roi_summary
    assert len(state.roi_rects) == 5
    assert state.access_profile.can_run_cycle is True
    assert state.camera_connected is True
    assert state.plc_connected is True
    assert state.recent_history_summaries == []


def test_main_presenter_loads_recent_history_from_repository() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    container.repository.save_inspection_history(
        InspectionHistoryRecord(
            recorded_at=datetime(2026, 4, 11, 11, 5, 0),
            user_name="admin",
            product_name="PRODUCT-A",
            overall_status="pass",
            plc_result_sent="OK",
            task_count=5,
            ok_count=5,
            ng_count=0,
        )
    )
    presenter = _build_main_presenter(container)

    state = presenter.load()

    assert len(state.recent_history_summaries) == 1
    assert "PRODUCT-A" in state.recent_history_summaries[0]
    assert "result=OK" in state.recent_history_summaries[0]
    assert "trigger=<none>" in state.recent_history_summaries[0]


def test_desktop_shell_launches_login_then_transitions_to_main_after_submit() -> None:
    container = build_container()
    container.repository.save_user(UserRecord(user_name="operator4", password_hash="pw", role="Operator"))
    container.repository.upsert_product(
        ProductRecord(product_name="PRODUCT-A", model_path="models/product_a.pt")
    )
    container.repository.update_session(product_name="PRODUCT-A")
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


def test_desktop_shell_applies_recording_default_from_runtime_settings() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(record_results_default=True))
    shell = DesktopShell(container=container)

    assert shell.main_presenter.runtime_controls.recording_enabled is True


def test_desktop_shell_can_open_existing_external_path(monkeypatch, tmp_path: Path) -> None:
    container = build_container()
    shell = DesktopShell(container=container)
    target = tmp_path / "artifact.json"
    target.write_text("{}", encoding="utf-8")
    calls: list[str] = []

    monkeypatch.setattr(os, "startfile", lambda value: calls.append(value))

    success, message = shell.open_external_path(str(target))

    assert success is True
    assert calls == [str(target)]
    assert str(target) in message


def test_desktop_shell_rejects_missing_external_path() -> None:
    container = build_container()
    shell = DesktopShell(container=container)

    success, message = shell.open_external_path("")

    assert success is False
    assert "not available" in message.lower()


def test_main_presenter_can_run_cycle_for_selected_product() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=True))
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.run_cycle()

    assert state.last_cycle_status == "pass"
    assert "OK" in state.message
    assert state.plc_last_result == "OK"
    assert state.task_summaries
    assert "match=forward" in state.task_summaries[0]
    assert "reason=text_match" in state.task_summaries[0]
    assert "source=detected_override" in state.task_summaries[0]
    assert state.last_quantity == 5
    assert state.last_ok_count == 5
    assert state.last_ng_count == 0
    assert state.last_result_label == "OK"
    assert state.last_trigger_source == "manual"
    assert state.last_cycle_duration_ms >= 0.0
    assert state.inspection_total_count == 5
    assert state.inspection_counter_value == 5
    assert state.inspection_batch_value == 0
    assert len(state.preview_annotations) == 5
    assert state.preview_annotations[0].label == "PRODUCT-A"
    assert state.preview_annotations[0].status == "pass"
    assert state.ocr_diagnostics
    assert "match=forward" in state.ocr_diagnostics[0]
    assert "reason=text_match" in state.ocr_diagnostics[0]
    assert "source=detected_override" in state.ocr_diagnostics[0]
    assert "warning=<none>" in state.ocr_diagnostics[0]
    assert "raw=<none>" in state.ocr_diagnostics[0]
    assert "row=20.0" in state.ocr_diagnostics[0]


def test_main_presenter_run_cycle_populates_artifact_summary_when_recording_is_enabled(tmp_path) -> None:
    container = build_container(
        runtime_settings=AppRuntimeSettings(
            demo_mode=True,
            artifact_root_dir=str(tmp_path),
        )
    )
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)
    presenter.toggle_recording_enabled()

    state = presenter.run_cycle()

    assert "artifacts saved" in state.message
    assert state.artifact_summary.startswith("Artifacts saved | summary=")
    assert " | overlay=" in state.artifact_summary
    assert state.last_artifact_dir
    assert state.latest_summary_path
    assert state.latest_task_artifacts
    assert state.latest_task_artifacts[0].task_id == "ocr_label_1"
    assert state.latest_task_artifacts[0].debug_path


def test_main_presenter_does_not_count_empty_ocr_text_in_runtime_metrics() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=False))
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    class _EmptyTextPerformCycle:
        def execute(self, recipe):
            return InspectionCycleResult(
                image_ref=ImageFrame(frame=[[0, 1], [2, 3]], capture_seconds=0.01),
                inspection=InspectionRunResult(
                    recipe_name=recipe.name,
                    overall_status=TaskStatus.PASS,
                    task_results=[
                        InspectionTaskResult(
                            task_id="ocr_label_1",
                            task_type=InspectionTaskType.OCR,
                            status=TaskStatus.SKIPPED,
                            message="OCR text was empty for expected product.",
                            outputs={
                                "text": "",
                                "matched_text": "",
                                "expected_text": "PRODUCT-A",
                                "roi_rect": (0, 0, 2, 2),
                                "reason": "empty_text",
                                "source": "runtime",
                                "counted_quantity": False,
                            },
                        )
                    ],
                    message="",
                ),
                plc_result_sent="OK",
                artifacts=None,
                trigger_source="manual",
                duration_ms=1.0,
                signal_summary="",
            )

    container.run_current_product_cycle.perform_cycle = _EmptyTextPerformCycle()

    state = presenter.run_cycle()

    assert state.last_cycle_status == "pass"
    assert state.last_quantity == 0
    assert state.last_ok_count == 0
    assert state.last_ng_count == 0
    assert state.inspection_total_count == 0
    assert state.last_result_label == "OK"
    assert state.plc_last_result == "OK"
    assert state.preview_annotations == []


def test_main_presenter_hides_mismatched_ocr_text_from_preview_overlay() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=False))
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    class _MismatchPerformCycle:
        def execute(self, recipe):
            return InspectionCycleResult(
                image_ref=ImageFrame(frame=[[0, 1], [2, 3]], capture_seconds=0.01),
                inspection=InspectionRunResult(
                    recipe_name=recipe.name,
                    overall_status=TaskStatus.FAIL,
                    task_results=[
                        InspectionTaskResult(
                            task_id="ocr_label_1",
                            task_type=InspectionTaskType.OCR,
                            status=TaskStatus.FAIL,
                            message="OCR text did not match expected product.",
                            outputs={
                                "text": "WRONG-TEXT",
                                "matched_text": "",
                                "expected_text": "PRODUCT-A",
                                "roi_rect": (0, 0, 2, 2),
                                "reason": "text_mismatch",
                                "source": "runtime",
                                "counted_quantity": True,
                            },
                        )
                    ],
                    message="",
                ),
                plc_result_sent="NG",
                artifacts=None,
                trigger_source="manual",
                duration_ms=1.0,
                signal_summary="",
            )

    container.run_current_product_cycle.perform_cycle = _MismatchPerformCycle()

    state = presenter.run_cycle()

    assert len(state.preview_annotations) == 1
    assert state.preview_annotations[0].status == "fail"
    assert state.preview_annotations[0].label == ""
    assert state.last_quantity == 1
    assert state.last_ng_count == 1


def test_main_presenter_can_grab_preview_frame() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.grab_preview_frame()

    assert state.preview_frame is not None
    assert "Frame source:" in state.preview_summary


def test_main_presenter_can_update_current_product_settings() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.update_product_settings(
        product_name="PRODUCT-A",
        model_path="models/product_a_v2.pt",
        default_number=200,
        exposure=4200,
        threshold_accept=0.8,
        threshold_mns=0.2,
    )

    assert state.model_path == "models/product_a_v2.pt"
    assert state.default_number == 200
    assert state.exposure == 4200
    assert state.threshold_accept == 0.8
    assert state.threshold_mns == 0.2
    assert state.message == "Product settings saved."


def test_main_presenter_can_import_product_catalog(tmp_path) -> None:
    catalog_path = tmp_path / "product_catalog.csv"
    catalog_path.write_text(
        "Product name,Model path,Exposure,Default number,Threshold accept,MNS threshold\n"
        "PRODUCT-B,models/product_b.pt,3900,170,0.7,0.2\n"
        "PRODUCT-C,models/product_c.pt,4100,180,0.8,0.3\n",
        encoding="utf-8",
    )
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.import_product_catalog_from_file(str(catalog_path))

    assert "Imported product catalog: 2 products." == state.message
    assert "PRODUCT-B" in state.available_products
    assert "PRODUCT-C" in state.available_products


def test_main_presenter_can_move_single_roi() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.move_roi(direction="left", roi_index=2, move_all=False)

    session = container.load_session_settings.execute().session
    assert session.roi_x1 == 760
    assert session.roi_x2 == 1240
    assert state.message == "Moved ROI 2 left."
    assert state.roi_points[1] == (1240, 1180)


def test_main_presenter_can_poll_plc_once_in_idle_state() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.poll_plc_once()

    assert state.plc_poll_action == "idle"
    assert state.plc_signal_summary == "PLC signals: grab=0 stop=0 start=0"


def test_main_presenter_can_toggle_auto_and_inspection_modes() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    auto_state = presenter.set_auto_mode()
    inspection_state = presenter.toggle_inspection_enabled()
    recording_state = presenter.toggle_recording_enabled()
    manual_state = presenter.set_manual_mode()

    assert auto_state.auto_mode_enabled is True
    assert inspection_state.inspection_enabled is True
    assert recording_state.recording_enabled is True
    assert manual_state.auto_mode_enabled is False


def test_main_presenter_start_signal_enables_ai_checking() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)
    presenter.set_auto_mode()
    presenter.poll_plc_signals.plc.read_inputs_once = lambda: PlcReadState(start_requested=True)

    state = presenter.poll_plc_once()

    assert state.plc_poll_action == "start"
    assert state.inspection_enabled is True


def test_main_presenter_poll_grab_does_not_run_cycle_when_ai_checking_is_disabled() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)
    presenter.poll_plc_signals.previous_state = PlcReadState()
    presenter.poll_plc_signals.plc.read_inputs_once = lambda: PlcReadState(grab_requested=True)

    state = presenter.poll_plc_once()

    assert state.plc_poll_action == "grab"
    assert state.plc_cycle_triggered is False
    assert state.last_cycle_status == ""


def test_main_presenter_can_disconnect_and_reconnect_camera() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    disconnected = presenter.disconnect_camera_hardware()
    connected = presenter.connect_camera_hardware()

    assert disconnected.camera_connected is False
    assert disconnected.message == "Camera disconnected."
    assert connected.camera_connected is True
    assert connected.message == "Camera connected."


def test_main_presenter_can_disconnect_and_reconnect_plc() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    disconnected = presenter.disconnect_plc_hardware()
    connected = presenter.connect_plc_hardware()

    assert disconnected.plc_connected is False
    assert disconnected.message == "PLC disconnected."
    assert connected.plc_connected is True
    assert connected.message == "PLC connected."


def test_main_presenter_can_shutdown_runtime_hardware() -> None:
    container = build_container()
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)

    state = presenter.shutdown_runtime_hardware()

    assert state.camera_connected is False
    assert state.plc_connected is False
    assert state.message == "Runtime shutdown completed."


def test_main_presenter_can_reset_cycle_counters() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=True))
    _seed_main_screen_state(container)
    presenter = _build_main_presenter(container)
    presenter.run_cycle()

    state = presenter.reset_cycle_counters()

    assert state.inspection_total_count == 0
    assert state.inspection_counter_value == 0
    assert state.inspection_batch_value == 0
    assert state.last_quantity == 0
    assert state.last_ok_count == 0
    assert state.last_ng_count == 0
    assert state.last_result_label == ""
    assert state.message == "Inspection counters reset."


def test_selecting_product_resets_cycle_counters() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=True))
    _seed_main_screen_state(container)
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-B",
            model_path="models/product_b.pt",
            default_number=200,
            exposure=3600,
            threshold_accept=0.6,
            threshold_mns=0.4,
        )
    )
    presenter = _build_main_presenter(container)
    presenter.run_cycle()

    state = presenter.select_current_product("PRODUCT-B")

    assert state.selected_product_name == "PRODUCT-B"
    assert state.inspection_total_count == 0
    assert state.last_quantity == 0
