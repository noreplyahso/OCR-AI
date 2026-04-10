from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraSettings, CameraVendor


@dataclass
class CameraAdapter:
    connection_settings: CameraConnectionSettings = field(default_factory=CameraConnectionSettings)
    settings: CameraSettings = field(default_factory=CameraSettings)

    @property
    def vendor(self) -> CameraVendor:
        return self.connection_settings.vendor

    def configure_connection(self, settings: CameraConnectionSettings) -> None:
        self.connection_settings = settings

    def apply_settings(self, settings: CameraSettings) -> None:
        self.settings = settings

    def connect(self) -> bool:
        return True

    def disconnect(self) -> None:
        return None

    def is_connected(self) -> bool:
        return True

    def grab(self) -> ImageFrame:
        return ImageFrame(frame="frame://placeholder", capture_seconds=0.0)
