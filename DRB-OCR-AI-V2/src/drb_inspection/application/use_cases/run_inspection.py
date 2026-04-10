from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.inspection import InspectionRunResult
from drb_inspection.domain.inspection.models import InspectionRecipe
from drb_inspection.domain.inspection.pipeline import InspectionPipeline


@dataclass
class RunInspectionUseCase:
    pipeline: InspectionPipeline
    repository: RepositoryAdapter

    def execute(self, recipe: InspectionRecipe, image_ref: object) -> InspectionRunResult:
        self.repository.record_event(f"Run inspection for recipe={recipe.name} image_ref={image_ref}")
        return self.pipeline.run(recipe=recipe, image_ref=image_ref)
