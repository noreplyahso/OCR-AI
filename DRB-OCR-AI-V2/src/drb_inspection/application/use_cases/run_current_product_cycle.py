from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from drb_inspection.adapters.db.models import InspectionHistoryRecord
from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.application.contracts.inspection import InspectionCycleResult
from drb_inspection.application.services.current_product_recipe_builder import CurrentProductRecipeBuilder
from drb_inspection.application.services.inspection_artifact_recorder import InspectionArtifactRecorder
from drb_inspection.application.use_cases.configure_camera import ConfigureCurrentCameraUseCase
from drb_inspection.application.use_cases.perform_cycle import PerformInspectionCycleUseCase


@dataclass
class RunCurrentProductCycleUseCase:
    repository: RepositoryAdapter
    configure_camera: ConfigureCurrentCameraUseCase
    perform_cycle: PerformInspectionCycleUseCase
    runtime_settings: AppRuntimeSettings
    recipe_builder: CurrentProductRecipeBuilder
    artifact_recorder: InspectionArtifactRecorder | None = None

    def execute(
        self,
        *,
        record_results: bool | None = None,
        trigger_source: str = "manual",
        signal_summary: str = "",
    ) -> InspectionCycleResult:
        session = self.repository.get_session()
        product_name = session.product_name.strip()
        if not product_name:
            raise ValueError("Current product is None.")

        product = self.repository.get_product(product_name)
        if product is None:
            raise ValueError("Invalid product.")

        self.configure_camera.execute()
        recipe = self.recipe_builder.build(session=session, product=product)
        cycle = self.perform_cycle.execute(recipe=recipe)
        cycle.trigger_source = trigger_source
        cycle.signal_summary = signal_summary
        detailed_recording_enabled = (
            self.runtime_settings.record_results_default if record_results is None else bool(record_results)
        )
        should_record = self._should_record_artifacts(cycle)
        if should_record and self.artifact_recorder is not None:
            try:
                cycle.artifacts = self.artifact_recorder.record_cycle(
                    product_name=product.product_name,
                    session=session,
                    cycle_result=cycle,
                    include_task_artifacts=detailed_recording_enabled,
                )
            except Exception as exc:
                self.repository.record_event(f"Inspection artifact save failed: {exc}")
        self.repository.save_inspection_history(
            self._build_history_entry(
                user_name=session.user_name,
                product_name=product.product_name,
                cycle=cycle,
            )
        )
        self.repository.record_event(
            f"Run current product cycle product={product.product_name} status={cycle.inspection.overall_status.value}"
        )
        if cycle.artifacts is not None:
            self.repository.record_event(f"Inspection artifacts saved root={cycle.artifacts.root_dir}")
        return cycle

    def _build_history_entry(
        self,
        *,
        user_name: str,
        product_name: str,
        cycle: InspectionCycleResult,
    ) -> InspectionHistoryRecord:
        counted_results = [
            task_result
            for task_result in cycle.inspection.task_results
            if self._task_counted_for_history(task_result)
        ]
        task_count = len(counted_results)
        ok_count = sum(
            1
            for task_result in counted_results
            if task_result.status.value == "pass"
        )
        ng_count = max(0, task_count - ok_count)
        return InspectionHistoryRecord(
            recorded_at=datetime.now(),
            user_name=user_name,
            product_name=product_name,
            recipe_name=cycle.inspection.recipe_name,
            overall_status=cycle.inspection.overall_status.value,
            plc_result_sent=cycle.plc_result_sent,
            trigger_source=cycle.trigger_source,
            cycle_duration_ms=cycle.duration_ms,
            signal_summary=cycle.signal_summary,
            task_count=task_count,
            ok_count=ok_count,
            ng_count=ng_count,
            message=cycle.inspection.message,
            artifact_dir=cycle.artifacts.root_dir if cycle.artifacts is not None else "",
        )

    def _task_counted_for_history(self, task_result) -> bool:
        if task_result.task_type.value != "ocr":
            return True
        counted = task_result.outputs.get("counted_quantity")
        if isinstance(counted, bool):
            return counted
        text = str(task_result.outputs.get("text", "")).strip()
        return bool(text)

    def _should_record_artifacts(self, cycle: InspectionCycleResult) -> bool:
        has_ocr_tasks = any(
            task_result.task_type.value == "ocr"
            for task_result in cycle.inspection.task_results
        )
        if not has_ocr_tasks:
            return bool(cycle.inspection.task_results)
        return any(
            self._task_counted_for_history(task_result)
            for task_result in cycle.inspection.task_results
            if task_result.task_type.value == "ocr"
        )
