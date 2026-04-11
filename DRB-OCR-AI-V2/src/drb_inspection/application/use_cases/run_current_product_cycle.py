from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.contracts.inspection import InspectionCycleResult, InspectionTaskType
from drb_inspection.application.services.inspection_artifact_recorder import InspectionArtifactRecorder
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.perform_cycle import PerformInspectionCycleUseCase
from drb_inspection.domain.inspection.models import InspectionRecipe, RecipeStep


@dataclass
class RunCurrentProductCycleUseCase:
    repository: RepositoryAdapter
    configure_camera: ConfigureCurrentCameraUseCase
    perform_cycle: PerformInspectionCycleUseCase
    runtime_settings: AppRuntimeSettings
    artifact_recorder: InspectionArtifactRecorder | None = None

    def execute(self, *, record_results: bool | None = None) -> InspectionCycleResult:
        session = self.repository.get_session()
        product_name = session.product_name.strip()
        if not product_name:
            raise ValueError("Current product is None.")

        product = self.repository.get_product(product_name)
        if product is None:
            raise ValueError("Invalid product.")

        self.configure_camera.execute()
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
                        "acceptance_threshold": (
                            product.threshold_accept if product.threshold_accept is not None else 0.8
                        ),
                        "duplication_threshold": (
                            product.threshold_mns if product.threshold_mns is not None else 0.5
                        ),
                        **({"detected_text": product.product_name} if self.runtime_settings.demo_mode else {}),
                    },
                )
            )
        recipe = InspectionRecipe(
            name=f"inspection-{product.product_name}",
            version=1,
            steps=steps,
        )
        cycle = self.perform_cycle.execute(recipe=recipe)
        should_record = self.runtime_settings.record_results_default if record_results is None else bool(record_results)
        if should_record and self.artifact_recorder is not None:
            cycle.artifacts = self.artifact_recorder.record_cycle(
                product_name=product.product_name,
                session=session,
                cycle_result=cycle,
            )
        self.repository.record_event(
            f"Run current product cycle product={product.product_name} status={cycle.inspection.overall_status.value}"
        )
        if cycle.artifacts is not None:
            self.repository.record_event(f"Inspection artifacts saved root={cycle.artifacts.root_dir}")
        return cycle
