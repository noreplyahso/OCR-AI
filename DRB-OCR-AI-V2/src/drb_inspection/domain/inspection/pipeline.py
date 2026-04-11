from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.inspection import (
    InspectionRunResult,
    InspectionTaskRequest,
    InspectionTaskResult,
    TaskStatus,
)
from drb_inspection.domain.inspection.models import InspectionRecipe
from drb_inspection.plugins.registry import PluginRegistry
from drb_inspection.workers.local_ai_worker import LocalAiWorker


@dataclass
class InspectionPipeline:
    worker: LocalAiWorker
    plugin_registry: PluginRegistry

    def run(self, recipe: InspectionRecipe, image_ref: object) -> InspectionRunResult:
        results: list[InspectionTaskResult] = []
        for step in recipe.steps:
            plugin = self.plugin_registry.get(step.plugin)
            request = InspectionTaskRequest(
                task_id=step.step_id,
                task_type=step.task_type,
                image_ref=image_ref,
                roi_name=step.roi_name,
                parameters=self._build_parameters(step.parameters, image_ref=image_ref),
            )
            results.append(self.worker.execute(plugin=plugin, request=request))
        return InspectionRunResult(
            recipe_name=recipe.name,
            overall_status=self._evaluate(recipe=recipe, results=results),
            task_results=results,
        )

    def _build_parameters(self, step_parameters: dict[str, object], *, image_ref: object) -> dict[str, object]:
        parameters = dict(step_parameters)
        parameters.setdefault("image_ref", image_ref)
        if hasattr(image_ref, "frame"):
            parameters.setdefault("frame", image_ref.frame)
            capture_seconds = getattr(image_ref, "capture_seconds", None)
            if capture_seconds is not None:
                parameters.setdefault("capture_seconds", capture_seconds)
        elif not isinstance(image_ref, str):
            parameters.setdefault("image", image_ref)
        return parameters

    def _evaluate(self, recipe: InspectionRecipe, results: list[InspectionTaskResult]) -> TaskStatus:
        result_by_id = {result.task_id: result for result in results}
        for step in recipe.steps:
            result = result_by_id.get(step.step_id)
            if not step.required:
                continue
            if result is None:
                return TaskStatus.ERROR
            if result.status == TaskStatus.ERROR:
                return TaskStatus.ERROR
            if result.status == TaskStatus.SKIPPED:
                continue
            if result.status != TaskStatus.PASS:
                return TaskStatus.FAIL
        return TaskStatus.PASS
