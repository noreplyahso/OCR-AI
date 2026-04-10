import os

from drb_inspection.adapters.camera.base import CameraAdapter
from drb_inspection.adapters.camera.models import CameraConnectionSettings
from drb_inspection.adapters.camera.models import CameraVendor
from drb_inspection.adapters.camera.pylon_camera import PylonCameraAdapter
from drb_inspection.adapters.camera.vendor_sdk_camera import HikrobotCameraAdapter, IraypleCameraAdapter, OptCameraAdapter
from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType, PlcVendor
from drb_inspection.adapters.plc.protocol_adapter import ProtocolPlcAdapter
from drb_inspection.adapters.plc.profiles import resolve_signal_map
from drb_inspection.app.container import build_container
from drb_inspection.app.settings import AppRuntimeSettings, load_runtime_settings


def test_load_runtime_settings_reads_env_flags() -> None:
    keys = [
        "DRB_V2_HEADLESS",
        "DRB_V2_USE_PYLON",
        "DRB_V2_CAMERA_VENDOR",
        "DRB_V2_CAMERA_SERIAL",
        "DRB_V2_DEMO_MODE",
        "DRB_V2_USE_LEGACY_OCR_RUNTIME",
        "DRB_V2_OCR_RUNTIME_DIR",
        "DRB_V2_PLC_VENDOR",
        "DRB_V2_PLC_PROTOCOL",
        "DRB_V2_PLC_IP",
        "DRB_V2_PLC_PORT",
    ]
    previous = {key: os.environ.get(key) for key in keys}
    try:
        os.environ["DRB_V2_HEADLESS"] = "1"
        os.environ["DRB_V2_CAMERA_VENDOR"] = "hikrobot"
        os.environ["DRB_V2_CAMERA_SERIAL"] = "CAM-001"
        os.environ["DRB_V2_DEMO_MODE"] = "1"
        os.environ["DRB_V2_USE_LEGACY_OCR_RUNTIME"] = "1"
        os.environ["DRB_V2_OCR_RUNTIME_DIR"] = "C:/runtime"
        os.environ["DRB_V2_PLC_VENDOR"] = "mitsubishi"
        os.environ["DRB_V2_PLC_PROTOCOL"] = "slmp"
        os.environ["DRB_V2_PLC_IP"] = "192.168.3.39"
        os.environ["DRB_V2_PLC_PORT"] = "5000"
        settings = load_runtime_settings()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.headless is True
    assert settings.demo_mode is True
    assert settings.use_legacy_ocr_runtime is True
    assert settings.ocr_runtime_dir == "C:/runtime"
    assert settings.camera_connection.vendor == CameraVendor.HIKROBOT
    assert settings.camera_connection.serial_number == "CAM-001"
    assert settings.plc_connection.vendor == PlcVendor.MITSUBISHI
    assert settings.plc_connection.protocol_type == PlcProtocolType.SLMP
    assert settings.plc_connection.ip == "192.168.3.39"
    assert settings.plc_connection.port == 5000


def test_mitsubishi_defaults_to_slmp_when_protocol_is_not_explicit() -> None:
    keys = ["DRB_V2_PLC_VENDOR", "DRB_V2_PLC_PROTOCOL", "DRB_V2_PLC_PORT"]
    previous = {key: os.environ.get(key) for key in keys}
    try:
        os.environ["DRB_V2_PLC_VENDOR"] = "mitsubishi"
        os.environ.pop("DRB_V2_PLC_PROTOCOL", None)
        os.environ.pop("DRB_V2_PLC_PORT", None)
        settings = load_runtime_settings()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert settings.plc_connection.vendor == PlcVendor.MITSUBISHI
    assert settings.plc_connection.protocol_type == PlcProtocolType.SLMP
    assert settings.plc_connection.port == 5000


def test_build_container_uses_selected_camera_and_plc_adapters() -> None:
    demo_container = build_container(runtime_settings=AppRuntimeSettings())
    basler_slmp_container = build_container(
        runtime_settings=AppRuntimeSettings(
            camera_connection=CameraConnectionSettings(vendor=CameraVendor.BASLER),
            plc_connection=PlcConnectionSettings(
                vendor=PlcVendor.MITSUBISHI,
                protocol_type=PlcProtocolType.SLMP,
                signal_map=resolve_signal_map(PlcVendor.MITSUBISHI),
            ),
        )
    )

    assert isinstance(demo_container.camera, CameraAdapter)
    assert isinstance(demo_container.plc, PlcAdapter)
    assert isinstance(basler_slmp_container.camera, PylonCameraAdapter)
    assert isinstance(basler_slmp_container.plc, ProtocolPlcAdapter)


def test_build_container_supports_other_camera_vendors() -> None:
    hikrobot_container = build_container(
        runtime_settings=AppRuntimeSettings(
            camera_connection=CameraConnectionSettings(vendor=CameraVendor.HIKROBOT)
        )
    )
    irayple_container = build_container(
        runtime_settings=AppRuntimeSettings(
            camera_connection=CameraConnectionSettings(vendor=CameraVendor.IRAYPLE)
        )
    )
    opt_container = build_container(
        runtime_settings=AppRuntimeSettings(
            camera_connection=CameraConnectionSettings(vendor=CameraVendor.OPT)
        )
    )

    assert isinstance(hikrobot_container.camera, HikrobotCameraAdapter)
    assert isinstance(irayple_container.camera, IraypleCameraAdapter)
    assert isinstance(opt_container.camera, OptCameraAdapter)
