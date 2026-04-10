from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor
from drb_inspection.adapters.camera.pylon_camera import PylonCameraAdapter


class _DeviceInfo:
    def __init__(self, serial: str, ip: str):
        self._serial = serial
        self._ip = ip

    def GetSerialNumber(self):
        return self._serial

    def GetIpAddress(self):
        return self._ip


def test_basler_adapter_selects_device_by_serial_number() -> None:
    adapter = PylonCameraAdapter(
        connection_settings=CameraConnectionSettings(
            vendor=CameraVendor.BASLER,
            serial_number="BASLER-002",
        )
    )
    devices = [
        _DeviceInfo("BASLER-001", "192.168.0.10"),
        _DeviceInfo("BASLER-002", "192.168.0.11"),
    ]

    device = adapter._select_device(devices)

    assert device is devices[1]


def test_basler_adapter_selects_device_by_ip_address() -> None:
    adapter = PylonCameraAdapter(
        connection_settings=CameraConnectionSettings(
            vendor=CameraVendor.BASLER,
            ip_address="192.168.0.11",
        )
    )
    devices = [
        _DeviceInfo("BASLER-001", "192.168.0.10"),
        _DeviceInfo("BASLER-002", "192.168.0.11"),
    ]

    device = adapter._select_device(devices)

    assert device is devices[1]


def test_basler_adapter_returns_none_when_configured_device_not_found() -> None:
    adapter = PylonCameraAdapter(
        connection_settings=CameraConnectionSettings(
            vendor=CameraVendor.BASLER,
            serial_number="BASLER-003",
        )
    )
    devices = [
        _DeviceInfo("BASLER-001", "192.168.0.10"),
        _DeviceInfo("BASLER-002", "192.168.0.11"),
    ]

    device = adapter._select_device(devices)

    assert device is None
