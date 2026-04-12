from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.adapters.plc.models import PlcReadState
from drb_inspection.application.contracts.inspection import InspectionCycleResult, InspectionRunResult


@dataclass(frozen=True)
class RuntimeStatus:
    camera_vendor: str
    camera_connected: bool
    plc_vendor: str
    plc_protocol: str
    plc_connected: bool
    plc_last_result: str = ""


@dataclass(frozen=True)
class PreviewFrameResult:
    image_frame: ImageFrame | None
    camera_connected: bool
    message: str = ""


@dataclass(frozen=True)
class PreviewInspectionResult:
    image_frame: ImageFrame | None
    camera_connected: bool
    inspection: InspectionRunResult | None = None
    duration_ms: float = 0.0
    message: str = ""


@dataclass(frozen=True)
class RuntimeHardwareResult:
    success: bool
    camera_connected: bool
    plc_connected: bool
    message: str = ""


@dataclass(frozen=True)
class PlcPollResult:
    read_state: PlcReadState
    action: str = "idle"
    cycle_result: InspectionCycleResult | None = None
    cycle_triggered: bool = False
    signal_summary: str = ""
    message: str = ""
