from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.inspection import (
    InspectionTaskRequest,
    InspectionTaskResult,
    TaskStatus,
)


@dataclass
class SegmentPlugin:
    name: str = "segment"

    def run(self, request: InspectionTaskRequest) -> InspectionTaskResult:
        mask_ratio = float(request.parameters.get("mask_threshold", 0.5))
        return InspectionTaskResult(
            task_id=request.task_id,
            task_type=request.task_type,
            status=TaskStatus.PASS,
            score=mask_ratio,
            message="Placeholder segment plugin executed.",
            outputs={"mask_ratio": mask_ratio},
        )
