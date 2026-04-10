from drb_inspection.app.container import build_container
from drb_inspection.app.settings import AppRuntimeSettings
from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor
from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.models import ImageFrame
from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType, PlcVendor
from drb_inspection.adapters.plc.profiles import resolve_signal_map
from drb_inspection.application.use_cases.grab_preview import GrabPreviewUseCase


def test_load_runtime_status_reflects_camera_and_plc_state() -> None:
    container = build_container(
        runtime_settings=AppRuntimeSettings(
            camera_connection=CameraConnectionSettings(vendor=CameraVendor.BASLER),
            plc_connection=PlcConnectionSettings(
                vendor=PlcVendor.MITSUBISHI,
                protocol_type=PlcProtocolType.SLMP,
                signal_map=resolve_signal_map(PlcVendor.MITSUBISHI),
            ),
        )
    )

    status = container.load_runtime_status.execute()

    assert status.camera_vendor == "basler"
    assert status.camera_connected is False
    assert status.plc_vendor == "mitsubishi"
    assert status.plc_protocol == "slmp"
    assert status.plc_connected is False
    assert status.plc_last_result == ""


def test_grab_preview_returns_frame_and_message() -> None:
    container = build_container()

    preview = container.grab_preview.execute()

    assert preview.image_frame is not None
    assert preview.message == "Preview frame captured."


def test_grab_preview_attempts_to_connect_camera_when_disconnected() -> None:
    class _ConnectOnDemandCamera(CameraAdapter):
        def __init__(self):
            self.connected = False
            self.connect_calls = 0

        def is_connected(self) -> bool:
            return self.connected

        def connect(self) -> bool:
            self.connect_calls += 1
            self.connected = True
            return True

        def grab(self) -> ImageFrame:
            return ImageFrame(frame="frame://connected", capture_seconds=0.01)

    use_case = GrabPreviewUseCase(camera=_ConnectOnDemandCamera())

    preview = use_case.execute()

    assert preview.camera_connected is True
    assert preview.image_frame is not None
    assert preview.image_frame.frame == "frame://connected"
