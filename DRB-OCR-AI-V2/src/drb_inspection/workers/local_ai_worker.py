from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.application.contracts.inspection import InspectionTaskRequest, InspectionTaskResult


@dataclass
class LocalAiWorker:
    """Local execution boundary for AI tasks.

    Later this can be replaced by a remote worker without changing the UI shell.
    """

    def execute(self, plugin: object, request: InspectionTaskRequest) -> InspectionTaskResult:
        return plugin.run(request)

