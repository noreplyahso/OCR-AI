from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.application.contracts.runtime import RuntimeHardwareResult


@dataclass
class ConnectCameraUseCase:
    camera: CameraAdapter
    plc: PlcAdapter

    def execute(self) -> RuntimeHardwareResult:
        try:
            success = bool(self.camera.connect())
        except Exception as exc:
            return RuntimeHardwareResult(
                success=False,
                camera_connected=False,
                plc_connected=self.plc.is_connected(),
                message=f"Camera connect failed: {exc}",
            )
        return RuntimeHardwareResult(
            success=success,
            camera_connected=self.camera.is_connected(),
            plc_connected=self.plc.is_connected(),
            message="Camera connected." if success else "Camera connect failed.",
        )
