from typing import Optional

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


class _Node:
    def __init__(self, *, minimum: int, maximum: int, increment: int = 1, value: Optional[int] = None):
        self.minimum = minimum
        self.maximum = maximum
        self.increment = increment
        self.value = minimum if value is None else value

    def GetMin(self):
        return self.minimum

    def GetMax(self):
        return self.maximum

    def GetInc(self):
        return self.increment

    def SetValue(self, value: int):
        self.value = value

    def GetValue(self):
        return self.value


class _FakeCamera:
    def __init__(self):
        self.OffsetX = _Node(minimum=0, maximum=92, increment=4, value=0)
        self.OffsetY = _Node(minimum=0, maximum=1440, increment=2, value=0)
        self.Width = _Node(minimum=16, maximum=2500, increment=4, value=2500)
        self.Height = _Node(minimum=16, maximum=1000, increment=2, value=1000)
        self.stop_calls = 0
        self.start_calls = 0

    def IsOpen(self):
        return True

    def StopGrabbing(self):
        self.stop_calls += 1

    def StartGrabbing(self, _strategy):
        self.start_calls += 1


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


def test_basler_adapter_coerces_integer_node_value_to_device_limits() -> None:
    adapter = PylonCameraAdapter()
    node = _Node(minimum=0, maximum=92, increment=4)

    assert adapter._coerce_integer_node_value(node, 300) == 92
    assert adapter._coerce_integer_node_value(node, 91) == 88
    assert adapter._coerce_integer_node_value(node, -10) == 0


def test_basler_adapter_clamps_image_size_and_offsets_to_camera_bounds() -> None:
    adapter = PylonCameraAdapter()
    adapter.camera = _FakeCamera()
    adapter._load_pylon = lambda: type("_Pylon", (), {"GrabStrategy_LatestImageOnly": object()})()

    adapter.set_image_size(offset_x=300, offset_y=1501, width=2500, height=1000)

    assert adapter.camera.stop_calls == 1
    assert adapter.camera.start_calls == 1
    assert adapter.camera.OffsetX.GetValue() == 92
    assert adapter.camera.OffsetY.GetValue() == 1440
    assert adapter.camera.Width.GetValue() == 2500
    assert adapter.camera.Height.GetValue() == 1000
    assert adapter.settings.offset_x == 92
    assert adapter.settings.offset_y == 1440
