from __future__ import annotations

import importlib
from dataclasses import dataclass, field

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor


@dataclass
class VendorSdkCameraAdapter(CameraAdapter):
    sdk_modules: tuple[str, ...] = field(default_factory=tuple)
    connected: bool = False
    last_error: str = ""

    def connect(self) -> bool:
        if self.connected:
            return True

        for module_name in self.sdk_modules:
            try:
                importlib.import_module(module_name)
            except ImportError:
                continue
            self.last_error = (
                f"{self.vendor.value} SDK detected but camera connect flow is not implemented yet."
            )
            self.connected = False
            return False

        self.last_error = f"{self.vendor.value} SDK is not available in the current environment."
        self.connected = False
        return False

    def disconnect(self) -> None:
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected


class HikrobotCameraAdapter(VendorSdkCameraAdapter):
    def __init__(self, connection_settings: CameraConnectionSettings | None = None):
        super().__init__(
            connection_settings=connection_settings or CameraConnectionSettings(vendor=CameraVendor.HIKROBOT),
            sdk_modules=("MvCameraControl_class", "hikrobot_sdk"),
        )


class IraypleCameraAdapter(VendorSdkCameraAdapter):
    def __init__(self, connection_settings: CameraConnectionSettings | None = None):
        super().__init__(
            connection_settings=connection_settings or CameraConnectionSettings(vendor=CameraVendor.IRAYPLE),
            sdk_modules=("MVSDK", "irayple_sdk"),
        )


class OptCameraAdapter(VendorSdkCameraAdapter):
    def __init__(self, connection_settings: CameraConnectionSettings | None = None):
        super().__init__(
            connection_settings=connection_settings or CameraConnectionSettings(vendor=CameraVendor.OPT),
            sdk_modules=("OPTCamera", "opt_camera_sdk"),
        )
