from pathlib import Path

from drb_inspection.application.contracts.inspection import InspectionTaskType
from drb_inspection.application.services.recipe_loader import RecipeLoader


def test_recipe_loader_parses_example_recipe() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    loader = RecipeLoader()

    recipe = loader.load_from_file(recipe_path)

    assert recipe.name == "sample-ocr-segment-recipe"
    assert recipe.version == 1
    assert len(recipe.steps) == 2
    assert recipe.steps[0].task_type == InspectionTaskType.OCR
    assert recipe.steps[1].task_type == InspectionTaskType.SEGMENT
    assert recipe.decision_mode == "all_required_pass"

