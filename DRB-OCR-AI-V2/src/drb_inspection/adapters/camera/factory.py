from __future__ import annotations

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor
from drb_inspection.adapters.camera.pylon_camera import PylonCameraAdapter
from drb_inspection.adapters.camera.vendor_sdk_camera import (
    HikrobotCameraAdapter,
    IraypleCameraAdapter,
    OptCameraAdapter,
)


def build_camera_adapter(
    connection_settings: CameraConnectionSettings | None = None,
) -> CameraAdapter:
    settings = connection_settings or CameraConnectionSettings()
    if settings.vendor == CameraVendor.BASLER:
        return PylonCameraAdapter(connection_settings=settings)
    if settings.vendor == CameraVendor.HIKROBOT:
        return HikrobotCameraAdapter(connection_settings=settings)
    if settings.vendor == CameraVendor.IRAYPLE:
        return IraypleCameraAdapter(connection_settings=settings)
    if settings.vendor == CameraVendor.OPT:
        return OptCameraAdapter(connection_settings=settings)
    return CameraAdapter(connection_settings=settings)
