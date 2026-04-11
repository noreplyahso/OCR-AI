from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.application.contracts.runtime import RuntimeHardwareResult


@dataclass
class ShutdownRuntimeUseCase:
    camera: CameraAdapter
    plc: PlcAdapter

    def execute(self) -> RuntimeHardwareResult:
        try:
            self.plc.set_light(False)
        except Exception:
            pass

        errors: list[str] = []
        try:
            self.camera.disconnect()
        except Exception as exc:
            errors.append(f"camera={exc}")
        try:
            self.plc.disconnect()
        except Exception as exc:
            errors.append(f"plc={exc}")

        if errors:
            return RuntimeHardwareResult(
                success=False,
                camera_connected=self.camera.is_connected(),
                plc_connected=self.plc.is_connected(),
                message="Runtime shutdown completed with errors: " + "; ".join(errors),
            )
        return RuntimeHardwareResult(
            success=True,
            camera_connected=self.camera.is_connected(),
            plc_connected=self.plc.is_connected(),
            message="Runtime shutdown completed.",
        )
