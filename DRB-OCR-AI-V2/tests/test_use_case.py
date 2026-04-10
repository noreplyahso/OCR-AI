from pathlib import Path

from drb_inspection.app.container import build_container
from drb_inspection.application.services.recipe_loader import RecipeLoader


def test_run_inspection_use_case_records_repository_event() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "examples" / "recipes" / "ocr_segment_recipe.yaml"
    container = build_container()
    recipe = RecipeLoader().load_from_file(recipe_path)

    container.run_inspection.execute(recipe=recipe, image_ref="frame://case-1")

    assert len(container.repository.events) == 1
    assert "sample-ocr-segment-recipe" in container.repository.events[0]
