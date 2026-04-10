from __future__ import annotations

from pathlib import Path

import yaml

from drb_inspection.application.contracts.inspection import InspectionTaskType
from drb_inspection.domain.inspection.models import InspectionRecipe, RecipeStep


class RecipeLoader:
    def load_from_file(self, path: str | Path) -> InspectionRecipe:
        recipe_path = Path(path)
        payload = yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
        return self.load_from_dict(payload)

    def load_from_dict(self, payload: dict) -> InspectionRecipe:
        steps = []
        for raw_step in payload.get("steps", []):
            steps.append(
                RecipeStep(
                    step_id=raw_step["id"],
                    plugin=raw_step["plugin"],
                    task_type=InspectionTaskType(raw_step["task_type"]),
                    roi_name=raw_step["roi"],
                    required=bool(raw_step.get("required", True)),
                    parameters=dict(raw_step.get("parameters", {})),
                )
            )

        decision = payload.get("decision", {})
        return InspectionRecipe(
            name=payload["name"],
            version=int(payload["version"]),
            steps=steps,
            decision_mode=str(decision.get("mode", "all_required_pass")),
        )
