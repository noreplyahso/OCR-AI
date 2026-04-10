from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.application.contracts.runtime import RuntimeStatus


@dataclass
class LoadRuntimeStatusUseCase:
    camera: CameraAdapter
    plc: PlcAdapter

    def execute(self) -> RuntimeStatus:
        return RuntimeStatus(
            camera_vendor=self.camera.connection_settings.vendor.value,
            camera_connected=self.camera.is_connected(),
            plc_vendor=self.plc.connection_settings.vendor.value,
            plc_protocol=self.plc.connection_settings.protocol_type.value,
            plc_connected=self.plc.is_connected(),
            plc_last_result=self.plc.last_result(),
        )
