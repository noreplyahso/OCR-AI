from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.contracts.inspection import InspectionCycleResult, InspectionTaskType
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.perform_cycle import PerformInspectionCycleUseCase
from drb_inspection.domain.inspection.models import InspectionRecipe, RecipeStep


@dataclass
class RunCurrentProductCycleUseCase:
    repository: RepositoryAdapter
    configure_camera: ConfigureCurrentCameraUseCase
    perform_cycle: PerformInspectionCycleUseCase
    runtime_settings: AppRuntimeSettings

    def execute(self) -> InspectionCycleResult:
        session = self.repository.get_session()
        product_name = session.product_name.strip()
        if not product_name:
            raise ValueError("Current product is None.")

        product = self.repository.get_product(product_name)
        if product is None:
            raise ValueError("Invalid product.")

        self.configure_camera.execute()
        recipe = InspectionRecipe(
            name=f"inspection-{product.product_name}",
            version=1,
            steps=[
                RecipeStep(
                    step_id="ocr_label",
                    plugin="ocr",
                    task_type=InspectionTaskType.OCR,
                    roi_name="label_roi",
                    required=True,
                    parameters={
                        "expected_text": product.product_name,
                        "model_path": product.model_path,
                        **({"detected_text": product.product_name} if self.runtime_settings.demo_mode else {}),
                    },
                )
            ],
        )
        cycle = self.perform_cycle.execute(recipe=recipe)
        self.repository.record_event(
            f"Run current product cycle product={product.product_name} status={cycle.inspection.overall_status.value}"
        )
        return cycle
