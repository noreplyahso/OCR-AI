from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.inspection import (
    InspectionTaskRequest,
    InspectionTaskResult,
    TaskStatus,
)


@dataclass
class ClassifyPlugin:
    name: str = "classify"

    def run(self, request: InspectionTaskRequest) -> InspectionTaskResult:
        predicted_class = str(request.parameters.get("class_name", "unknown"))
        return InspectionTaskResult(
            task_id=request.task_id,
            task_type=request.task_type,
            status=TaskStatus.PASS,
            score=float(request.parameters.get("score", 1.0)),
            message="Placeholder classify plugin executed.",
            outputs={"class_name": predicted_class},
        )
