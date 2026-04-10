from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.models import ImageFrame


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
