from pathlib import Path

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.app.container import build_container
from drb_inspection.application.contracts.inspection import TaskStatus
from drb_inspection.application.services.recipe_loader import RecipeLoader
from drb_inspection.domain.inspection.models import InspectionRecipe, RecipeStep
from drb_inspection.application.contracts.inspection import InspectionTaskType


def test_pipeline_runs_recipe_and_returns_pass_summary() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    container = build_container()
    loader = RecipeLoader()
    recipe = loader.load_from_file(recipe_path)

    run_result = container.run_inspection.execute(recipe=recipe, image_ref="frame://test")

    assert run_result.recipe_name == "sample-ocr-segment-recipe"
    assert run_result.overall_status == TaskStatus.PASS
    assert len(run_result.task_results) == 2
    assert run_result.task_results[0].outputs["text"] == "PRODUCT-A"


def test_pipeline_injects_image_frame_into_ocr_step_parameters() -> None:
    container = build_container()
    recipe = InspectionRecipe(
        name="frame-aware-ocr",
        version=1,
        steps=[
            RecipeStep(
                step_id="ocr_frame",
                plugin="ocr",
                task_type=InspectionTaskType.OCR,
                roi_name="label_roi",
                parameters={
                    "roi_rect": (1, 0, 2, 3),
                    "detected_text": "IS35R-100",
                    "expected_text": "IS35R-100",
                },
            )
        ],
    )
    image_frame = ImageFrame(
        frame=[
            ["x", "I", "S"],
            ["x", "3", "5"],
            ["x", "R", "-"],
            ["x", "1", "0"],
        ],
        capture_seconds=0.015,
    )

    run_result = container.run_inspection.execute(recipe=recipe, image_ref=image_frame)

    assert run_result.overall_status == TaskStatus.PASS
    assert run_result.task_results[0].outputs["matched_text"] == "IS35R-100"


def test_pipeline_propagates_error_for_required_step() -> None:
    container = build_container()
    recipe = InspectionRecipe(
        name="required-error",
        version=1,
        steps=[
            RecipeStep(
                step_id="ocr_error",
                plugin="ocr",
                task_type=InspectionTaskType.OCR,
                roi_name="label_roi",
                parameters={
                    "expected_text": "IS35R-100",
                },
            )
        ],
    )

    run_result = container.run_inspection.execute(recipe=recipe, image_ref="frame://test")

    assert run_result.overall_status == TaskStatus.ERROR
    assert run_result.task_results[0].status == TaskStatus.ERROR
