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
    assert result.trigger_source == "manual"
    assert len(spy.captured_recipe.steps) == 5
    assert first_step.parameters["model_path"] == "models/product_x.pt"
    assert first_step.parameters["row_threshold"] == 20
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
    assert result.artifacts.annotated_frame_path
    assert Path(result.artifacts.annotated_frame_path).exists()
    assert len(result.artifacts.task_artifacts) == 1
    assert result.artifacts.task_artifacts[0].debug_path
    assert Path(result.artifacts.task_artifacts[0].debug_path).exists()
    assert result.trigger_source == "manual"


def test_run_current_product_cycle_records_core_artifacts_when_detailed_recording_is_disabled(
    tmp_path: Path,
) -> None:
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

    result = container.run_current_product_cycle.execute(record_results=False)

    assert result.artifacts is not None
    assert Path(result.artifacts.summary_path).exists()
    assert Path(result.artifacts.frame_path).exists()
    assert result.artifacts.annotated_frame_path
    assert Path(result.artifacts.annotated_frame_path).exists()
    assert result.artifacts.task_artifacts == []


def test_run_current_product_cycle_persists_history_entry_to_repository() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=True))
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-H",
            model_path="models/product_h.pt",
        )
    )
    container.repository.update_session(user_name="admin", product_name="PRODUCT-H")

    result = container.run_current_product_cycle.execute()
    history = container.repository.list_recent_inspection_history(limit=1)

    assert result.plc_result_sent == "OK"
    assert len(history) == 1
    assert history[0].product_name == "PRODUCT-H"
    assert history[0].plc_result_sent == "OK"
    assert history[0].task_count == 5
    assert history[0].trigger_source == "manual"
    assert history[0].cycle_duration_ms >= 0.0


def test_run_current_product_cycle_does_not_count_skipped_ocr_in_history() -> None:
    container = build_container(runtime_settings=AppRuntimeSettings(demo_mode=False))
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-S",
            model_path="models/product_s.pt",
        )
    )
    container.repository.update_session(user_name="admin", product_name="PRODUCT-S")

    @dataclass
    class _SkippedPerformCycle:
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
                                "expected_text": "PRODUCT-S",
                                "counted_quantity": False,
                            },
                        )
                    ],
                    message="",
                ),
                plc_result_sent="OK",
            )

    container.run_current_product_cycle.perform_cycle = _SkippedPerformCycle()

    result = container.run_current_product_cycle.execute()
    history = container.repository.list_recent_inspection_history(limit=1)

    assert result.plc_result_sent == "OK"
    assert len(history) == 1
    assert history[0].overall_status == "pass"
    assert history[0].task_count == 0


def test_run_current_product_cycle_does_not_fail_when_artifact_recording_raises() -> None:
    container = build_container(
        runtime_settings=AppRuntimeSettings(
            demo_mode=False,
            artifact_root_dir="C:/invalid-artifact-dir",
        )
    )
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-Z",
            model_path="models/product_z.pt",
        )
    )
    container.repository.update_session(user_name="admin", product_name="PRODUCT-Z")

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
                                "text": "PRODUCT-Z",
                                "expected_text": "PRODUCT-Z",
                                "counted_quantity": True,
                            },
                        )
                    ],
                    message="ok",
                ),
                plc_result_sent="OK",
            )

    class _BrokenArtifactRecorder:
        def record_cycle(self, **kwargs):
            raise PermissionError("artifact root is not writable")

    container.run_current_product_cycle.perform_cycle = _ArtifactPerformCycle()
    container.run_current_product_cycle.artifact_recorder = _BrokenArtifactRecorder()

    result = container.run_current_product_cycle.execute(record_results=True)
    history = container.repository.list_recent_inspection_history(limit=1)

    assert result.plc_result_sent == "OK"
    assert result.artifacts is None
    assert len(history) == 1
    assert history[0].ok_count == 1
    assert any("Inspection artifact save failed:" in event for event in container.repository.events)
    assert history[0].ng_count == 0


def test_run_current_product_cycle_does_not_record_artifacts_when_ocr_quantity_is_zero(
    tmp_path: Path,
) -> None:
    container = build_container(
        runtime_settings=AppRuntimeSettings(
            demo_mode=False,
            artifact_root_dir=str(tmp_path),
        )
    )
    container.repository.upsert_product(
        ProductRecord(
            product_name="PRODUCT-S",
            model_path="models/product_s.pt",
        )
    )
    container.repository.update_session(user_name="admin", product_name="PRODUCT-S")

    @dataclass
    class _SkippedPerformCycle:
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
                                "expected_text": "PRODUCT-S",
                                "counted_quantity": False,
                            },
                        )
                    ],
                    message="",
                ),
                plc_result_sent="OK",
            )

    container.run_current_product_cycle.perform_cycle = _SkippedPerformCycle()

    result = container.run_current_product_cycle.execute(record_results=True)

    assert result.plc_result_sent == "OK"
    assert result.artifacts is None
