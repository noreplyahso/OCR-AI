from pathlib import Path

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.app.container import build_container
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.contracts.inspection import (
    InspectionRunResult,
    InspectionTaskResult,
    InspectionTaskType,
    TaskStatus,
)
from drb_inspection.application.services.recipe_loader import RecipeLoader
from drb_inspection.application.use_cases.perform_cycle import PerformInspectionCycleUseCase
from drb_inspection.application.use_cases.run_inspection import RunInspectionUseCase
from drb_inspection.domain.inspection.pipeline import InspectionPipeline
from drb_inspection.plugins.registry import PluginRegistry
from drb_inspection.workers.local_ai_worker import LocalAiWorker


def test_perform_cycle_grabs_image_runs_pipeline_and_sends_ok() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    container = build_container()
    recipe = RecipeLoader().load_from_file(recipe_path)

    cycle_result = container.perform_cycle.execute(recipe=recipe)

    assert cycle_result.image_ref.frame == "frame://placeholder"
    assert cycle_result.inspection.overall_status == TaskStatus.PASS
    assert cycle_result.plc_result_sent == "OK"
    assert container.plc.sent_results == ["OK"]


def test_perform_cycle_returns_ng_when_camera_frame_unavailable() -> None:
    class _MissingCamera(CameraAdapter):
        def grab(self):
            return None

    container = build_container(runtime_settings=AppRuntimeSettings())
    run_inspection = RunInspectionUseCase(
        pipeline=InspectionPipeline(
            worker=LocalAiWorker(),
            plugin_registry=PluginRegistry({}),
        ),
        repository=container.repository,
    )
    use_case = PerformInspectionCycleUseCase(
        camera=_MissingCamera(),
        plc=container.plc,
        run_inspection=run_inspection,
    )
    recipe = RecipeLoader().load_from_file(
        Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    )

    cycle_result = use_case.execute(recipe=recipe)

    assert cycle_result.image_ref is None
    assert cycle_result.inspection.overall_status == TaskStatus.ERROR
    assert cycle_result.plc_result_sent == "NG"


def test_perform_cycle_attempts_camera_connect_when_disconnected() -> None:
    class _ConnectOnDemandCamera(CameraAdapter):
        def __init__(self):
            self.connected = False
            self.connect_calls = 0

        def is_connected(self) -> bool:
            return self.connected

        def connect(self) -> bool:
            self.connect_calls += 1
            self.connected = True
            return True

    recipe_path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    container = build_container()
    recipe = RecipeLoader().load_from_file(recipe_path)
    use_case = PerformInspectionCycleUseCase(
        camera=_ConnectOnDemandCamera(),
        plc=container.plc,
        run_inspection=container.run_inspection,
    )

    cycle_result = use_case.execute(recipe=recipe)

    assert cycle_result.inspection.overall_status == TaskStatus.PASS
    assert cycle_result.plc_result_sent == "OK"


def test_perform_cycle_sends_ok_when_required_tasks_are_skipped() -> None:
    class _SkipRunInspection:
        def execute(self, recipe, image_ref):
            return InspectionRunResult(
                recipe_name=recipe.name,
                overall_status=TaskStatus.PASS,
                task_results=[
                    InspectionTaskResult(
                        task_id="ocr_skip",
                        task_type=InspectionTaskType.OCR,
                        status=TaskStatus.SKIPPED,
                        message="OCR text was empty.",
                        outputs={"counted_quantity": False, "text": ""},
                    )
                ],
            )

    recipe_path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    container = build_container()
    recipe = RecipeLoader().load_from_file(recipe_path)
    use_case = PerformInspectionCycleUseCase(
        camera=container.camera,
        plc=container.plc,
        run_inspection=_SkipRunInspection(),
    )

    cycle_result = use_case.execute(recipe=recipe)

    assert cycle_result.inspection.overall_status == TaskStatus.PASS
    assert cycle_result.plc_result_sent == "OK"
    assert container.plc.sent_results[-1] == "OK"
