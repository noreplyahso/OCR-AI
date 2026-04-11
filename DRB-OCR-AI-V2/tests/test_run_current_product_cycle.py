from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.adapters.db.models import ProductRecord
from drb_inspection.app.container import build_container
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.contracts.inspection import (
    InspectionCycleResult,
    InspectionRunResult,
    InspectionTaskResult,
    InspectionTaskType,
    TaskStatus,
)


@dataclass
class _SpyPerformCycle:
    captured_recipe: object | None = None

    def execute(self, recipe):
        self.captured_recipe = recipe
        return InspectionCycleResult(
            image_ref=ImageFrame(frame="frame://spy", capture_seconds=0.01),
            inspection=InspectionRunResult(
                recipe_name=recipe.name,
                overall_status=TaskStatus.PASS,
                task_results=[],
                message="spy",
            ),
            plc_result_sent="OK",
        )


def test_run_current_product_cycle_uses_product_configuration_in_recipe() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=False))
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-X",
            model_path="models/product_x.pt",
            exposure=4300,
            default_number=180,
            threshold_accept=0.9,
            threshold_mns=0.3,
        )
    )
    container.repository.update_session(
        product_name="PRODUCT-X",
        offset_x=300,
        offset_y=1400,
        roi_x1=760,
        roi_x2=1250,
        roi_x3=1730,
        roi_x4=2220,
        roi_x5=2710,
        roi_y1=1180,
        roi_y2=1180,
        roi_y3=1180,
        roi_y4=1180,
        roi_y5=1180,
    )
    spy = _SpyPerformCycle()
    container.run_current_product_cycle.perform_cycle = spy

    result = container.run_current_product_cycle.execute()
    first_step = spy.captured_recipe.steps[0]
    last_step = spy.captured_recipe.steps[-1]

    assert result.plc_result_sent == "OK"
    assert len(spy.captured_recipe.steps) == 5
    assert first_step.parameters["model_path"] == "models/product_x.pt"
    assert first_step.parameters["acceptance_threshold"] == 0.9
    assert first_step.parameters["duplication_threshold"] == 0.3
    assert first_step.parameters["roi_rect"] == (460, -220, 300, 440)
    assert last_step.parameters["roi_rect"] == (2410, -220, 300, 440)
    assert "detected_text" not in first_step.parameters


def test_run_current_product_cycle_records_artifacts_when_enabled(tmp_path: Path) -> None:
    container = build_container(
        runtime_settings=AppRuntimeSettings(
            demo_mode=False,
            artifact_root_dir=str(tmp_path),
        )
    )
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-X",
            model_path="models/product_x.pt",
        )
    )
    container.repository.update_session(product_name="PRODUCT-X")

    @dataclass
    class _ArtifactPerformCycle:
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
                            status=TaskStatus.PASS,
                            outputs={
                                "text": "PRODUCT-X",
                                "expected_text": "PRODUCT-X",
                                "roi_name": "label_roi_1",
                                "roi_rect": (0, 0, 2, 2),
                                "roi_image": [[255, 255], [0, 0]],
                            },
                        )
                    ],
                ),
                plc_result_sent="OK",
            )

    container.run_current_product_cycle.perform_cycle = _ArtifactPerformCycle()

    result = container.run_current_product_cycle.execute(record_results=True)

    assert result.artifacts is not None
    assert Path(result.artifacts.summary_path).exists()
    assert Path(result.artifacts.frame_path).exists()
    assert len(result.artifacts.task_artifacts) == 1
