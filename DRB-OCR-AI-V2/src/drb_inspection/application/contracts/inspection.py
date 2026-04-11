from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InspectionTaskType(str, Enum):
    OCR = "ocr"
    CLASSIFY = "classify"
    SEGMENT = "segment"


class TaskStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class InspectionTaskRequest:
    task_id: str
    task_type: InspectionTaskType
    image_ref: object
    roi_name: str
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass
class InspectionTaskResult:
    task_id: str
    task_type: InspectionTaskType
    status: TaskStatus
    score: float | None = None
    message: str = ""
    outputs: dict[str, object] = field(default_factory=dict)


@dataclass
class InspectionRunResult:
    recipe_name: str
    overall_status: TaskStatus
    task_results: list[InspectionTaskResult] = field(default_factory=list)
    message: str = ""


@dataclass(frozen=True)
class InspectionTaskArtifact:
    task_id: str
    image_path: str = ""


@dataclass(frozen=True)
class InspectionCycleArtifacts:
    root_dir: str
    summary_path: str
    frame_path: str = ""
    task_artifacts: list[InspectionTaskArtifact] = field(default_factory=list)


@dataclass
class InspectionCycleResult:
    image_ref: object
    inspection: InspectionRunResult
    plc_result_sent: str
    artifacts: InspectionCycleArtifacts | None = None
