from __future__ import annotations

import os
from dataclasses import dataclass

from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor
from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType, PlcVendor
from drb_inspection.adapters.plc.profiles import resolve_signal_map


@dataclass(frozen=True)
class AppRuntimeSettings:
    headless: bool = False
    demo_mode: bool = False
    auto_preview_on_start: bool = False
    use_legacy_ocr_runtime: bool = False
    ocr_runtime_dir: str | None = None
    camera_connection: CameraConnectionSettings = CameraConnectionSettings()
    plc_connection: PlcConnectionSettings = PlcConnectionSettings()


def _parse_camera_vendor() -> CameraVendor:
    raw = (os.environ.get("DRB_V2_CAMERA_VENDOR") or "").strip().lower()
    if raw:
        return CameraVendor(raw)
    if os.environ.get("DRB_V2_USE_PYLON") == "1":
        return CameraVendor.BASLER
    return CameraVendor.DEMO


def _parse_plc_vendor() -> PlcVendor:
    raw = (os.environ.get("DRB_V2_PLC_VENDOR") or "").strip().lower()
    if raw:
        return PlcVendor(raw)
    return PlcVendor.DEMO


def _parse_plc_protocol() -> PlcProtocolType:
    raw = (os.environ.get("DRB_V2_PLC_PROTOCOL") or "").strip().lower()
    if raw:
        return PlcProtocolType(raw)
    vendor = _parse_plc_vendor()
    if vendor == PlcVendor.MITSUBISHI:
        return PlcProtocolType.SLMP
    if vendor in {PlcVendor.SIEMENS, PlcVendor.DELTA, PlcVendor.GENERIC}:
        return PlcProtocolType.MODBUS_TCP
    return PlcProtocolType.DEMO


def _default_plc_port(protocol: PlcProtocolType) -> int:
    if protocol == PlcProtocolType.SLMP:
        return 5000
    if protocol == PlcProtocolType.MODBUS_TCP:
        return 502
    return 502


def load_runtime_settings() -> AppRuntimeSettings:
    camera_vendor = _parse_camera_vendor()
    plc_vendor = _parse_plc_vendor()
    plc_protocol = _parse_plc_protocol()
    plc_port = int(os.environ.get("DRB_V2_PLC_PORT", str(_default_plc_port(plc_protocol))))
    return AppRuntimeSettings(
        headless=os.environ.get("DRB_V2_HEADLESS") == "1",
        demo_mode=os.environ.get("DRB_V2_DEMO_MODE") == "1",
        auto_preview_on_start=os.environ.get("DRB_V2_AUTO_PREVIEW_ON_START") == "1",
        use_legacy_ocr_runtime=os.environ.get("DRB_V2_USE_LEGACY_OCR_RUNTIME") == "1",
        ocr_runtime_dir=os.environ.get("DRB_V2_OCR_RUNTIME_DIR"),
        camera_connection=CameraConnectionSettings(
            vendor=camera_vendor,
            serial_number=os.environ.get("DRB_V2_CAMERA_SERIAL", ""),
            ip_address=os.environ.get("DRB_V2_CAMERA_IP", ""),
            user_set=os.environ.get("DRB_V2_CAMERA_USER_SET", ""),
            sdk_path=os.environ.get("DRB_V2_CAMERA_SDK_PATH", ""),
            acquisition_mode=os.environ.get("DRB_V2_CAMERA_ACQUISITION_MODE", "continuous"),
        ),
        plc_connection=PlcConnectionSettings(
            vendor=plc_vendor,
            protocol_type=plc_protocol,
            ip=os.environ.get("DRB_V2_PLC_IP", "192.168.0.250"),
            port=plc_port,
            tries=int(os.environ.get("DRB_V2_PLC_TRIES", "1")),
            serial_port=os.environ.get("DRB_V2_PLC_SERIAL_PORT", "COM1"),
            baudrate=int(os.environ.get("DRB_V2_PLC_BAUDRATE", "9600")),
            parity=os.environ.get("DRB_V2_PLC_PARITY", "N"),
            stopbits=int(os.environ.get("DRB_V2_PLC_STOPBITS", "1")),
            bytesize=int(os.environ.get("DRB_V2_PLC_BYTESIZE", "8")),
            slave_id=int(os.environ.get("DRB_V2_PLC_SLAVE_ID", "1")),
            plc_type=os.environ.get("DRB_V2_PLC_TYPE", "Q"),
            comm_type=os.environ.get("DRB_V2_PLC_COMM_TYPE", "binary"),
            signal_map=resolve_signal_map(plc_vendor),
        ),
    )
