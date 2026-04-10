from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.application.contracts.inspection import InspectionCycleResult
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.grab_preview import GrabPreviewUseCase
from drb_inspection.application.use_cases.load_main_screen_context import LoadMainScreenContextUseCase
from drb_inspection.application.use_cases.load_runtime_status import LoadRuntimeStatusUseCase
from drb_inspection.application.use_cases.load_session_settings import LoadSessionSettingsUseCase
from drb_inspection.application.use_cases.run_current_product_cycle import RunCurrentProductCycleUseCase
from drb_inspection.application.use_cases.save_session_settings import SaveSessionSettingsUseCase
from drb_inspection.application.use_cases.select_product import SelectProductUseCase
from drb_inspection.ui.screens.main.state import MainScreenState


@dataclass
class MainScreenPresenter:
    load_main_screen_context: LoadMainScreenContextUseCase
    load_session_settings: LoadSessionSettingsUseCase
    load_runtime_status: LoadRuntimeStatusUseCase
    configure_camera: ConfigureCurrentCameraUseCase
    grab_preview: GrabPreviewUseCase
    save_session_settings: SaveSessionSettingsUseCase
    select_product: SelectProductUseCase
    run_current_product_cycle: RunCurrentProductCycleUseCase

    def load(self) -> MainScreenState:
        context = self.load_main_screen_context.execute()
        settings = self.load_session_settings.execute().session
        runtime = self.load_runtime_status.execute()
        return MainScreenState(
            current_user_name=context.current_user_name,
            current_role=context.current_role,
            available_products=context.available_products,
            selected_product_name=context.session.product_name,
            model_path=context.selected_model_path,
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
            access_profile=context.access_profile,
            camera_connected=runtime.camera_connected,
            plc_connected=runtime.plc_connected,
            plc_last_result=runtime.plc_last_result,
        )

    def select_current_product(self, product_name: str) -> MainScreenState:
        product_result = self.select_product.execute(product_name)
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "selected_product_name": product_result.product.product_name,
                "model_path": product_result.product.model_path,
                "message": f"Selected product: {product_result.product.product_name}",
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
        cycle_result = self.run_current_product_cycle.execute()
        state = self.load()
        return MainScreenState(
            **{
                **state.__dict__,
                "last_cycle_status": cycle_result.inspection.overall_status.value,
                "plc_last_result": cycle_result.plc_result_sent,
                "preview_frame": cycle_result.image_ref,
                "preview_summary": self._build_preview_summary(cycle_result.image_ref),
                "task_summaries": self._build_task_summaries(cycle_result),
                "message": self._build_cycle_message(cycle_result),
            }
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
        if cycle_result.inspection.message:
            return f"{base} | {cycle_result.inspection.message}"
        return base
