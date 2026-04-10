from __future__ import annotations

import time
from dataclasses import dataclass, field

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraSettings, CameraVendor, ImageFrame


@dataclass
class PylonCameraAdapter(CameraAdapter):
    connection_settings: CameraConnectionSettings = field(
        default_factory=lambda: CameraConnectionSettings(vendor=CameraVendor.BASLER)
    )
    settings: CameraSettings = field(default_factory=CameraSettings)
    camera: object | None = None
    _converter: object | None = None

    def _load_pylon(self):
        from pypylon import pylon

        return pylon

    def connect(self) -> bool:
        if self.is_connected():
            return True

        pylon = self._load_pylon()
        factory = pylon.TlFactory.GetInstance()
        devices = factory.EnumerateDevices()
        if not devices:
            return False

        device = self._select_device(devices)
        if device is None:
            return False

        self.camera = pylon.InstantCamera(factory.CreateDevice(device))
        self.camera.Open()
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        self._converter = pylon.ImageFormatConverter()
        self._converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self._converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        self.change_exposure(self.settings.exposure_time)
        if self.settings.width > 0 and self.settings.height > 0:
            self.set_image_size(
                offset_x=self.settings.offset_x,
                offset_y=self.settings.offset_y,
                width=self.settings.width,
                height=self.settings.height,
            )
        return True

    def disconnect(self) -> None:
        if self.camera is None:
            return
        try:
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()
            if self.camera.IsOpen():
                self.camera.Close()
        finally:
            self.camera = None

    def is_connected(self) -> bool:
        return bool(self.camera is not None and self.camera.IsOpen())

    def change_exposure(self, exposure_time: int) -> None:
        self.settings.exposure_time = exposure_time
        if not self.is_connected():
            return

        node_map = self.camera.GetNodeMap()
        exposure_node = node_map.GetNode("ExposureTimeAbs")
        if exposure_node is not None:
            self.camera.ExposureTimeAbs.SetValue(exposure_time)
        else:
            self.camera.ExposureTime.SetValue(exposure_time)
        self.settings.exposure_time = exposure_time

    def apply_settings(self, settings: CameraSettings) -> None:
        self.settings = settings
        if not self.is_connected():
            return
        self.change_exposure(settings.exposure_time)
        if settings.width > 0 and settings.height > 0:
            self.set_image_size(
                offset_x=settings.offset_x,
                offset_y=settings.offset_y,
                width=settings.width,
                height=settings.height,
            )

    def set_image_size(self, *, offset_x: int, offset_y: int, width: int, height: int) -> None:
        if not self.is_connected():
            return

        self.camera.StopGrabbing()
        self.camera.OffsetX.SetValue(0)
        self.camera.OffsetY.SetValue(0)
        self.camera.Width.SetValue(width)
        self.camera.Height.SetValue(height)
        self.camera.OffsetX.SetValue(offset_x)
        self.camera.OffsetY.SetValue(offset_y)
        self.camera.StartGrabbing(self._load_pylon().GrabStrategy_LatestImageOnly)
        self.settings = CameraSettings(
            exposure_time=self.settings.exposure_time,
            offset_x=offset_x,
            offset_y=offset_y,
            width=width,
            height=height,
        )

    def grab(self) -> ImageFrame | None:
        if not self.is_connected():
            return None

        pylon = self._load_pylon()
        start = time.time()
        grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        try:
            if not grab_result.GrabSucceeded():
                return None
            frame = self._converter.Convert(grab_result).GetArray()
            return ImageFrame(frame=frame, capture_seconds=time.time() - start)
        finally:
            grab_result.Release()

    def _select_device(self, devices):
        serial_number = self.connection_settings.serial_number.strip()
        ip_address = self.connection_settings.ip_address.strip()
        if not serial_number and not ip_address:
            return devices[0]

        for device in devices:
            if serial_number and self._device_value(device, "GetSerialNumber") == serial_number:
                return device
            if ip_address and self._device_value(device, "GetIpAddress") == ip_address:
                return device
        return None

    def _device_value(self, device, method_name: str) -> str:
        method = getattr(device, method_name, None)
        if method is None:
            return ""
        try:
            value = method()
        except Exception:
            return ""
        return "" if value is None else str(value)
