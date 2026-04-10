from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.application.contracts.inspection import InspectionCycleResult, InspectionRunResult, TaskStatus
from drb_inspection.application.use_cases.run_inspection import RunInspectionUseCase
from drb_inspection.domain.inspection.models import InspectionRecipe


@dataclass
class PerformInspectionCycleUseCase:
    camera: CameraAdapter
    plc: PlcAdapter
    run_inspection: RunInspectionUseCase

    def execute(self, recipe: InspectionRecipe) -> InspectionCycleResult:
        try:
            camera_connected = self.camera.is_connected()
            if not camera_connected:
                camera_connected = bool(self.camera.connect())
        except Exception as exc:
            inspection_result = InspectionRunResult(
                recipe_name=recipe.name,
                overall_status=TaskStatus.ERROR,
                task_results=[],
                message=f"Camera connect failed: {exc}",
            )
            plc_result = "NG"
            self.plc.send_result(plc_result)
            return InspectionCycleResult(
                image_ref=None,
                inspection=inspection_result,
                plc_result_sent=plc_result,
            )

        if not camera_connected:
            inspection_result = InspectionRunResult(
                recipe_name=recipe.name,
                overall_status=TaskStatus.ERROR,
                task_results=[],
                message="Camera is not connected.",
            )
            plc_result = "NG"
            self.plc.send_result(plc_result)
            return InspectionCycleResult(
                image_ref=None,
                inspection=inspection_result,
                plc_result_sent=plc_result,
            )

        image_frame = self.camera.grab()
        if image_frame is None:
            inspection_result = InspectionRunResult(
                recipe_name=recipe.name,
                overall_status=TaskStatus.ERROR,
                task_results=[],
                message="Camera frame unavailable.",
            )
            plc_result = "NG"
            self.plc.send_result(plc_result)
            return InspectionCycleResult(
                image_ref=image_frame,
                inspection=inspection_result,
                plc_result_sent=plc_result,
            )
        inspection_result = self.run_inspection.execute(recipe=recipe, image_ref=image_frame)
        plc_result = "OK" if inspection_result.overall_status == TaskStatus.PASS else "NG"
        self.plc.send_result(plc_result)
        return InspectionCycleResult(
            image_ref=image_frame,
            inspection=inspection_result,
            plc_result_sent=plc_result,
        )
