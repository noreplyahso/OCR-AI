from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.models import ProductRecord, SessionRecord
from drb_inspection.application.contracts.inspection import InspectionTaskType
from drb_inspection.domain.inspection.models import InspectionRecipe, RecipeStep


@dataclass(frozen=True)
class CurrentProductRecipeBuilder:
    demo_mode: bool = False

    def build(self, *, session: SessionRecord, product: ProductRecord) -> InspectionRecipe:
        steps = []
        for index, roi_rect in enumerate(session.roi_rects(), start=1):
            steps.append(
                RecipeStep(
                    step_id=f"ocr_label_{index}",
                    plugin="ocr",
                    task_type=InspectionTaskType.OCR,
                    roi_name=f"label_roi_{index}",
                    required=True,
                    parameters={
                        "expected_text": product.product_name,
                        "model_path": product.model_path,
                        "roi_rect": roi_rect,
                        "rotate_clockwise": True,
                        "row_threshold": 20,
                        "acceptance_threshold": (
                            product.threshold_accept if product.threshold_accept is not None else 0.8
                        ),
                        "duplication_threshold": (
                            product.threshold_mns if product.threshold_mns is not None else 0.5
                        ),
                        **({"detected_text": product.product_name} if self.demo_mode else {}),
                    },
                )
            )
        return InspectionRecipe(
            name=f"inspection-{product.product_name}",
            version=1,
            steps=steps,
        )
