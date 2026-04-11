from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.application.contracts.runtime import RuntimeHardwareResult


@dataclass
class ConnectPlcUseCase:
    camera: CameraAdapter
    plc: PlcAdapter

    def execute(self) -> RuntimeHardwareResult:
        try:
            success = bool(self.plc.connect())
        except Exception as exc:
            return RuntimeHardwareResult(
                success=False,
                camera_connected=self.camera.is_connected(),
                plc_connected=False,
                message=f"PLC connect failed: {exc}",
            )
        return RuntimeHardwareResult(
            success=success,
            camera_connected=self.camera.is_connected(),
            plc_connected=self.plc.is_connected(),
            message="PLC connected." if success else "PLC connect failed.",
        )
