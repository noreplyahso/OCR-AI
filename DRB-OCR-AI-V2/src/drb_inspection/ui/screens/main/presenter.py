from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.application.contracts.inspection import InspectionCycleResult
from drb_inspection.application.contracts.runtime import RuntimeHardwareResult
from drb_inspection.application.use_cases.connect_camera import ConnectCameraUseCase
from drb_inspection.application.use_cases.connect_plc import ConnectPlcUseCase
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.disconnect_camera import DisconnectCameraUseCase
from drb_inspection.application.use_cases.disconnect_plc import DisconnectPlcUseCase
from drb_inspection.application.use_cases.grab_preview import GrabPreviewUseCase
from drb_inspection.application.use_cases.import_product_catalog import ImportProductCatalogUseCase
from drb_inspection.application.use_cases.load_main_screen_context import LoadMainScreenContextUseCase
from drb_inspection.application.use_cases.load_runtime_status import LoadRuntimeStatusUseCase
from drb_inspection.application.use_cases.load_session_settings import LoadSessionSettingsUseCase
from drb_inspection.application.use_cases.move_session_roi import MoveSessionRoiUseCase
from drb_inspection.application.use_cases.poll_plc_signals import PollPlcSignalsUseCase
from drb_inspection.application.use_cases.run_current_product_cycle import RunCurrentProductCycleUseCase
from drb_inspection.application.use_cases.save_product_settings import SaveProductSettingsUseCase
from drb_inspection.application.use_cases.save_session_settings import SaveSessionSettingsUseCase
from drb_inspection.application.use_cases.select_product import SelectProductUseCase
from drb_inspection.application.use_cases.shutdown_runtime import ShutdownRuntimeUseCase
from drb_inspection.ui.screens.main.state import MainScreenState


@dataclass
class CycleRuntimeMetrics:
    total_count: int = 0
    counter_value: int = 0
    batch_value: int = 0
    last_quantity: int = 0
    last_ok_count: int = 0
    last_ng_count: int = 0
    last_result_label: str = ""


@dataclass
class RuntimeControlState:
    auto_mode_enabled: bool = False
    inspection_enabled: bool = False
    recording_enabled: bool = False
    artifact_summary: str = ""
    last_artifact_dir: str = ""


@dataclass
class MainScreenPresenter:
    load_main_screen_context: LoadMainScreenContextUseCase
    load_session_settings: LoadSessionSettingsUseCase
    load_runtime_status: LoadRuntimeStatusUseCase
    connect_camera: ConnectCameraUseCase
    disconnect_camera: DisconnectCameraUseCase
    connect_plc: ConnectPlcUseCase
    disconnect_plc: DisconnectPlcUseCase
    shutdown_runtime: ShutdownRuntimeUseCase
    configure_camera: ConfigureCurrentCameraUseCase
    grab_preview: GrabPreviewUseCase
    import_product_catalog: ImportProductCatalogUseCase
    save_session_settings: SaveSessionSettingsUseCase
    move_session_roi: MoveSessionRoiUseCase
    save_product_settings: SaveProductSettingsUseCase
    select_product: SelectProductUseCase
    run_current_product_cycle: RunCurrentProductCycleUseCase
    poll_plc_signals: PollPlcSignalsUseCase
    cycle_metrics: CycleRuntimeMetrics = field(default_factory=CycleRuntimeMetrics)
    runtime_controls: RuntimeControlState = field(default_factory=RuntimeControlState)

    def load(self) -> MainScreenState:
        context = self.load_main_screen_context.execute()
        settings = self.load_session_settings.execute().session
        runtime = self.load_runtime_status.execute()
        selected_product = context.selected_product
        return MainScreenState(
            current_user_name=context.current_user_name,
            current_role=context.current_role,
            available_products=context.available_products,
            selected_product_name=context.session.product_name,
            model_path=context.selected_model_path,
            default_number=selected_product.default_number if selected_product else None,
            exposure=selected_product.exposure if selected_product else None,
            threshold_accept=selected_product.threshold_accept if selected_product else None,
            threshold_mns=selected_product.threshold_mns if selected_product else None,
            camera_vendor=context.session.camera_vendor or runtime.camera_vendor,
            plc_vendor=context.session.plc_vendor or runtime.plc_vendor,
            plc_ip=settings.plc_ip,
            plc_port=str(settings.plc_port),
            plc_protocol=settings.plc_protocol,
            result_time=settings.result_time,
            sleep_time=settings.sleep_time,
            zoom_factor=settings.zoom_factor,
            offset_x=settings.offset_x,
            offset_y=settings.offset_y,
            image_width=settings.image_width,
            image_height=settings.image_height,
            roi_summary=self._build_roi_summary(settings),
            roi_points=settings.roi_points(),
            roi_rects=settings.roi_rects(),
            access_profile=context.access_profile,
            camera_connected=runtime.camera_connected,
            plc_connected=runtime.plc_connected,
            plc_last_result=runtime.plc_last_result,
            inspection_total_count=self.cycle_metrics.total_count,
            inspection_counter_value=self.cycle_metrics.counter_value,
            inspection_batch_value=self.cycle_metrics.batch_value,
            last_quantity=self.cycle_metrics.last_quantity,
            last_ok_count=self.cycle_metrics.last_ok_count,
            last_ng_count=self.cycle_metrics.last_ng_count,
            last_result_label=self.cycle_metrics.last_result_label,
            auto_mode_enabled=self.runtime_controls.auto_mode_enabled,
            inspection_enabled=self.runtime_controls.inspection_enabled,
            recording_enabled=self.runtime_controls.recording_enabled,
            artifact_summary=self.runtime_controls.artifact_summary,
            last_artifact_dir=self.runtime_controls.last_artifact_dir,
        )

    def select_current_product(self, product_name: str) -> MainScreenState:
        product_result = self.select_product.execute(product_name)
        self.clear_cycle_metrics()
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "selected_product_name": product_result.product.product_name,
                "model_path": product_result.product.model_path,
                "default_number": product_result.product.default_number,
                "exposure": product_result.product.exposure,
                "threshold_accept": product_result.product.threshold_accept,
                "threshold_mns": product_result.product.threshold_mns,
                "message": f"Selected product: {product_result.product.product_name}",
            }
        )

    def clear_cycle_metrics(self) -> None:
        self.cycle_metrics = CycleRuntimeMetrics()

    def clear_runtime_controls(self) -> None:
        self.runtime_controls = RuntimeControlState()

    def set_manual_mode(self) -> MainScreenState:
        self.runtime_controls.auto_mode_enabled = False
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "message": "Manual mode enabled.",
            }
        )

    def set_auto_mode(self) -> MainScreenState:
        self.runtime_controls.auto_mode_enabled = True
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "message": "Auto mode enabled. PLC polling started.",
            }
        )

    def toggle_inspection_enabled(self) -> MainScreenState:
        self.runtime_controls.inspection_enabled = not self.runtime_controls.inspection_enabled
        state = self.load()
        status = "enabled" if self.runtime_controls.inspection_enabled else "disabled"
        return MainScreenState(
            **{
                **state.__dict__,
                "message": f"AI checking {status}.",
            }
        )

    def toggle_recording_enabled(self) -> MainScreenState:
        self.runtime_controls.recording_enabled = not self.runtime_controls.recording_enabled
        state = self.load()
        status = "enabled" if self.runtime_controls.recording_enabled else "disabled"
        return MainScreenState(
            **{
                **state.__dict__,
                "message": f"Result recording {status}.",
            }
        )

    def reset_cycle_counters(self) -> MainScreenState:
        self.clear_cycle_metrics()
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "message": "Inspection counters reset.",
            }
        )

    def update_product_settings(self, **updates) -> MainScreenState:
        self.save_product_settings.execute(**updates)
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "message": "Product settings saved.",
            }
        )

    def connect_camera_hardware(self) -> MainScreenState:
        result = self.connect_camera.execute()
        return self._state_with_hardware_result(result)

    def disconnect_camera_hardware(self) -> MainScreenState:
        result = self.disconnect_camera.execute()
        return self._state_with_hardware_result(result)

    def connect_plc_hardware(self) -> MainScreenState:
        result = self.connect_plc.execute()
        return self._state_with_hardware_result(result)

    def disconnect_plc_hardware(self) -> MainScreenState:
        result = self.disconnect_plc.execute()
        return self._state_with_hardware_result(result)

    def shutdown_runtime_hardware(self) -> MainScreenState:
        result = self.shutdown_runtime.execute()
        return self._state_with_hardware_result(result)

    def import_product_catalog_from_file(self, path: str) -> MainScreenState:
        result = self.import_product_catalog.execute(path)
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "message": f"Imported product catalog: {len(result.products)} products.",
            }
        )

    def update_session_settings(self, **updates) -> MainScreenState:
        self.save_session_settings.execute(**updates)
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "message": "Session settings saved.",
            }
        )

    def move_roi(
        self,
        *,
        direction: str,
        roi_index: int,
        move_all: bool,
        step: int = 10,
    ) -> MainScreenState:
        self.move_session_roi.execute(
            direction=direction,
            roi_index=roi_index,
            move_all=move_all,
            step=step,
        )
        state = self.load()
        target_label = "all ROIs" if move_all else f"ROI {roi_index}"
        return MainScreenState(
            **{
                **state.__dict__,
                "message": f"Moved {target_label} {direction}.",
            }
        )

    def grab_preview_frame(self) -> MainScreenState:
        camera_result = self.configure_camera.execute()
        preview = self.grab_preview.execute()
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "preview_frame": preview.image_frame,
                "preview_summary": self._build_preview_summary(preview.image_frame),
                "camera_connected": preview.camera_connected,
                "message": f"{camera_result.message} {preview.message}",
            }
        )

    def run_cycle(self) -> MainScreenState:
        cycle_result = self.run_current_product_cycle.execute(
            record_results=self.runtime_controls.recording_enabled
        )
        state = self.load()
        return self._state_with_cycle_result(
            state=state,
            cycle_result=cycle_result,
            message=self._build_cycle_message(cycle_result),
        )

    def poll_plc_once(self) -> MainScreenState:
        poll_result = self.poll_plc_signals.execute(
            trigger_cycle=self.runtime_controls.inspection_enabled,
            record_results=self.runtime_controls.recording_enabled,
        )
        if poll_result.action == "start":
            self.runtime_controls.inspection_enabled = True
        elif poll_result.action == "stop":
            self.runtime_controls.inspection_enabled = False
        state = self.load()
        message = self._build_poll_message(
            message=poll_result.message,
            signal_summary=poll_result.signal_summary,
        )
        if poll_result.cycle_result is None:
            return MainScreenState(
                **{
                **state.__dict__,
                "plc_signal_summary": poll_result.signal_summary,
                "plc_poll_action": poll_result.action,
                "plc_cycle_triggered": poll_result.cycle_triggered,
                "inspection_enabled": self.runtime_controls.inspection_enabled,
                "message": message,
            }
        )
        return self._state_with_cycle_result(
            state=state,
            cycle_result=poll_result.cycle_result,
            message=message,
            plc_signal_summary=poll_result.signal_summary,
            plc_poll_action=poll_result.action,
            plc_cycle_triggered=poll_result.cycle_triggered,
        )

    def _build_preview_summary(self, image_frame: ImageFrame | None) -> str:
        if image_frame is None:
            return "No frame captured."

        frame = image_frame.frame
        shape = getattr(frame, "shape", None)
        if shape is not None:
            try:
                if len(shape) >= 2:
                    return (
                        f"Frame {int(shape[1])}x{int(shape[0])}"
                        f" | capture {image_frame.capture_seconds * 1000:.1f} ms"
                    )
            except (TypeError, ValueError):
                pass
        return f"Frame source: {frame!s} | capture {image_frame.capture_seconds * 1000:.1f} ms"

    def _build_task_summaries(self, cycle_result: InspectionCycleResult) -> list[str]:
        summaries: list[str] = []
        for task_result in cycle_result.inspection.task_results:
            text = str(task_result.outputs.get("text", "")).strip()
            expected = str(task_result.outputs.get("expected_text", "")).strip()
            details = f"{task_result.task_id}: {task_result.status.value.upper()}"
            if text:
                details += f" | text={text}"
            if expected:
                details += f" | expected={expected}"
            if task_result.message:
                details += f" | {task_result.message}"
            summaries.append(details)
        return summaries

    def _build_cycle_message(self, cycle_result: InspectionCycleResult) -> str:
        base = (
            f"Inspection cycle result: {cycle_result.plc_result_sent}"
            f" ({cycle_result.inspection.overall_status.value})"
        )
        if cycle_result.artifacts is not None:
            base = f"{base} | artifacts saved"
        if cycle_result.inspection.message:
            return f"{base} | {cycle_result.inspection.message}"
        return base

    def _build_poll_message(self, *, message: str, signal_summary: str) -> str:
        if signal_summary:
            return f"{message} | {signal_summary}"
        return message

    def _state_with_hardware_result(self, result: RuntimeHardwareResult) -> MainScreenState:
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "camera_connected": result.camera_connected,
                "plc_connected": result.plc_connected,
                "message": result.message,
            }
        )

    def _state_with_cycle_result(
        self,
        *,
        state: MainScreenState,
        cycle_result: InspectionCycleResult,
        message: str,
        plc_signal_summary: str = "",
        plc_poll_action: str = "",
        plc_cycle_triggered: bool = False,
    ) -> MainScreenState:
        self._update_cycle_metrics(
            cycle_result=cycle_result,
            default_number=state.default_number,
        )
        return MainScreenState(
            **{
                **state.__dict__,
                "last_cycle_status": cycle_result.inspection.overall_status.value,
                "plc_last_result": cycle_result.plc_result_sent,
                "plc_signal_summary": plc_signal_summary,
                "plc_poll_action": plc_poll_action,
                "plc_cycle_triggered": plc_cycle_triggered,
                "preview_frame": cycle_result.image_ref,
                "preview_summary": self._build_preview_summary(cycle_result.image_ref),
                "task_summaries": self._build_task_summaries(cycle_result),
                "inspection_total_count": self.cycle_metrics.total_count,
                "inspection_counter_value": self.cycle_metrics.counter_value,
                "inspection_batch_value": self.cycle_metrics.batch_value,
                "last_quantity": self.cycle_metrics.last_quantity,
                "last_ok_count": self.cycle_metrics.last_ok_count,
                "last_ng_count": self.cycle_metrics.last_ng_count,
                "last_result_label": self.cycle_metrics.last_result_label,
                "artifact_summary": self.runtime_controls.artifact_summary,
                "last_artifact_dir": self.runtime_controls.last_artifact_dir,
                "message": message,
            }
        )

    def _build_roi_summary(self, session) -> str:
        roi_points = session.roi_points()
        if not roi_points:
            return "ROIs: none"
        first_x, first_y = roi_points[0]
        last_x, last_y = roi_points[-1]
        return (
            f"ROIs: {len(roi_points)} zones"
            f" | first=({first_x},{first_y})"
            f" | last=({last_x},{last_y})"
        )

    def _update_cycle_metrics(
        self,
        *,
        cycle_result: InspectionCycleResult,
        default_number: int | None,
    ) -> None:
        quantity = len(cycle_result.inspection.task_results)
        ok_count = sum(
            1
            for task_result in cycle_result.inspection.task_results
            if task_result.status.value == "pass"
        )
        ng_count = max(0, quantity - ok_count)
        self.cycle_metrics.last_quantity = quantity
        self.cycle_metrics.last_ok_count = ok_count
        self.cycle_metrics.last_ng_count = ng_count
        self.cycle_metrics.last_result_label = (
            "OK" if cycle_result.inspection.overall_status.value == "pass" else "FAIL"
        )
        self.cycle_metrics.total_count += quantity
        normalized_default = max(1, int(default_number or quantity or 1))
        self.cycle_metrics.counter_value = self.cycle_metrics.total_count % normalized_default
        self.cycle_metrics.batch_value = self.cycle_metrics.total_count // normalized_default
        if cycle_result.artifacts is not None:
            frame_file = cycle_result.artifacts.frame_path or "<none>"
            self.runtime_controls.artifact_summary = (
                f"Artifacts saved | summary={cycle_result.artifacts.summary_path}"
                f" | frame={frame_file}"
                f" | tasks={len(cycle_result.artifacts.task_artifacts)}"
            )
            self.runtime_controls.last_artifact_dir = cycle_result.artifacts.root_dir
            return
        self.runtime_controls.artifact_summary = ""
        self.runtime_controls.last_artifact_dir = ""
