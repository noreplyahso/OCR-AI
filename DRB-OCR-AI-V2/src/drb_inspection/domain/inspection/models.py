from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.application.contracts.inspection import InspectionTaskType


@dataclass
class RecipeStep:
    step_id: str
    plugin: str
    task_type: InspectionTaskType
    roi_name: str
    required: bool = True
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass
class InspectionRecipe:
    name: str
    version: int
    steps: list[RecipeStep]
    decision_mode: str = "all_required_pass"
