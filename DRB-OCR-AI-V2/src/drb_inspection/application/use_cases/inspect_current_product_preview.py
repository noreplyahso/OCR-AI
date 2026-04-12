from __future__ import annotations

import time
from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.runtime import PreviewInspectionResult
from drb_inspection.application.services.current_product_recipe_builder import CurrentProductRecipeBuilder
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.grab_preview import GrabPreviewUseCase
from drb_inspection.application.use_cases.run_inspection import RunInspectionUseCase


@dataclass
class InspectCurrentProductPreviewUseCase:
    repository: RepositoryAdapter
    configure_camera: ConfigureCurrentCameraUseCase
    grab_preview: GrabPreviewUseCase
    run_inspection: RunInspectionUseCase
    recipe_builder: CurrentProductRecipeBuilder

    def execute(self) -> PreviewInspectionResult:
        started_at = time.perf_counter()
        session = self.repository.get_session()
        product_name = session.product_name.strip()
        if not product_name:
            return PreviewInspectionResult(
                image_frame=None,
                camera_connected=False,
                message="Current product is None.",
            )

        product = self.repository.get_product(product_name)
        if product is None:
            return PreviewInspectionResult(
                image_frame=None,
                camera_connected=False,
                message="Invalid product.",
            )

        camera_result = self.configure_camera.execute()
        preview = self.grab_preview.execute()
        if preview.image_frame is None:
            return PreviewInspectionResult(
                image_frame=None,
                camera_connected=preview.camera_connected,
                message=f"{camera_result.message} {preview.message}".strip(),
            )

        recipe = self.recipe_builder.build(session=session, product=product)
        inspection = self.run_inspection.execute(recipe=recipe, image_ref=preview.image_frame)
        return PreviewInspectionResult(
            image_frame=preview.image_frame,
            camera_connected=preview.camera_connected,
            inspection=inspection,
            duration_ms=(time.perf_counter() - started_at) * 1000.0,
            message=f"{camera_result.message} {preview.message}".strip(),
        )
