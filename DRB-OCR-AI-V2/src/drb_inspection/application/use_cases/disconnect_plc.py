from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.application.contracts.runtime import RuntimeHardwareResult


@dataclass
class DisconnectPlcUseCase:
    camera: CameraAdapter
    plc: PlcAdapter

    def execute(self) -> RuntimeHardwareResult:
        try:
            self.plc.set_light(False)
            self.plc.disconnect()
        except Exception as exc:
            return RuntimeHardwareResult(
                success=False,
                camera_connected=self.camera.is_connected(),
                plc_connected=self.plc.is_connected(),
                message=f"PLC disconnect failed: {exc}",
            )
        return RuntimeHardwareResult(
            success=True,
            camera_connected=self.camera.is_connected(),
            plc_connected=self.plc.is_connected(),
            message="PLC disconnected.",
        )
