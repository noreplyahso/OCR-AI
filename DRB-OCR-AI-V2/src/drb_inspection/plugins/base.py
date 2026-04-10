from __future__ import annotations

from typing import Protocol

from drb_inspection.application.contracts.inspection import InspectionTaskRequest, InspectionTaskResult


class InspectionPlugin(Protocol):
    name: str

    def run(self, request: InspectionTaskRequest) -> InspectionTaskResult:
        ...

