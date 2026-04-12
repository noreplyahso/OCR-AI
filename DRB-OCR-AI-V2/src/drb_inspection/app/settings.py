from __future__ import annotations

import os
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from drb_inspection.adapters.camera.models import CameraConnectionSettings, CameraVendor
from drb_inspection.adapters.db.models import DatabaseSettings, RepositoryBackend
from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType, PlcVendor
from drb_inspection.adapters.plc.profiles import resolve_signal_map


@dataclass(frozen=True)
class AppRuntimeSettings:
    headless: bool = False
    demo_mode: bool = False
    seed_demo_data: bool = False
    auto_preview_on_start: bool = False
    record_results_default: bool = False
    artifact_root_dir: str | None = None
    use_legacy_ocr_runtime: bool = False
    ocr_runtime_dir: str | None = None
    repository_backend: RepositoryBackend = RepositoryBackend.MEMORY
    database_settings: DatabaseSettings = field(default_factory=DatabaseSettings)
    camera_connection: CameraConnectionSettings = field(default_factory=CameraConnectionSettings)
    plc_connection: PlcConnectionSettings = field(default_factory=PlcConnectionSettings)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_repository_backend() -> RepositoryBackend:
    raw = (os.environ.get("DRB_V2_REPOSITORY_BACKEND") or "").strip().lower()
    if raw in {"", "memory", "in_memory", "in-memory"}:
        return RepositoryBackend.MEMORY
    if raw == "mysql":
        return RepositoryBackend.MYSQL
    raise ValueError(f"Unsupported repository backend: {raw}")


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
    return PlcVendor.MITSUBISHI


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


def _parse_legacy_v1_protocol(raw: str | None) -> PlcProtocolType | None:
    normalized = str(raw or "").strip().lower()
    if not normalized:
        return None
    if normalized in {"tcp", "modbus_tcp", "modbustcp"}:
        return PlcProtocolType.MODBUS_TCP
    if normalized in {"rtu", "modbus_rtu", "modbusrtu"}:
        return PlcProtocolType.MODBUS_RTU
    if normalized in {"slmp", "mc", "mcprotocol", "mc_protocol"}:
        return PlcProtocolType.SLMP
    return None


def _load_legacy_v1_session_defaults() -> dict[str, Any]:
    """
    Read PLC-related runtime defaults from V1 current_session when enabled.

    This keeps V2 aligned with the exact machine configuration that V1 is
    already using successfully, without forcing test code to depend on MySQL.
    """

    if not _env_flag("DRB_V2_SYNC_V1_SESSION"):
        return {}

    try:
        import pymysql
    except Exception:
        return {}

    host = os.environ.get("DRB_V2_DB_HOST", "localhost")
    port = int(os.environ.get("DRB_V2_DB_PORT", "3306"))
    user = os.environ.get("DRB_V2_DB_USER", "drb")
    password = os.environ.get("DRB_V2_DB_PASSWORD", "drb123456")
    database = os.environ.get("DRB_V2_DB_NAME", "drb_text")

    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT PLCIP, PLCPort, PLCProtocol, ResultTime, SleepTime
                    FROM current_session
                    WHERE ID=%s
                    """,
                    (1,),
                )
                row = cursor.fetchone() or {}
        finally:
            connection.close()
    except Exception:
        return {}

    protocol = _parse_legacy_v1_protocol(row.get("PLCProtocol"))
    defaults: dict[str, Any] = {}
    if row.get("PLCIP"):
        defaults["plc_ip"] = str(row["PLCIP"])
    if row.get("PLCPort") not in {None, ""}:
        defaults["plc_port"] = int(row["PLCPort"])
    if protocol is not None:
        defaults["plc_protocol"] = protocol
    if row.get("ResultTime") not in {None, ""}:
        defaults["result_time"] = int(row["ResultTime"])
    if row.get("SleepTime") not in {None, ""}:
        defaults["sleep_time"] = int(row["SleepTime"])
    return defaults


def _default_artifact_root_dir() -> str:
    return str(resolve_app_storage_root_dir() / "inspection-results")


def resolve_app_storage_root_dir() -> Path:
    candidates: list[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(Path(local_appdata) / "DRB-OCR-AI-V2")
    candidates.append(Path.cwd() / ".drb-ocr-ai-v2")
    candidates.append(Path(tempfile.gettempdir()) / "DRB-OCR-AI-V2")

    seen: set[str] = set()
    for candidate in candidates:
        candidate_key = str(candidate).lower()
        if candidate_key in seen:
            continue
        seen.add(candidate_key)
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path.cwd()


def load_runtime_settings() -> AppRuntimeSettings:
    legacy_defaults = _load_legacy_v1_session_defaults()
    camera_vendor = _parse_camera_vendor()
    plc_vendor = _parse_plc_vendor()
    plc_protocol = (
        PlcProtocolType((os.environ.get("DRB_V2_PLC_PROTOCOL") or "").strip().lower())
        if (os.environ.get("DRB_V2_PLC_PROTOCOL") or "").strip()
        else legacy_defaults.get("plc_protocol") or _parse_plc_protocol()
    )
    plc_port = int(
        os.environ.get(
            "DRB_V2_PLC_PORT",
            str(legacy_defaults.get("plc_port", _default_plc_port(plc_protocol))),
        )
    )
    repository_backend = _parse_repository_backend()
    return AppRuntimeSettings(
        headless=_env_flag("DRB_V2_HEADLESS"),
        demo_mode=_env_flag("DRB_V2_DEMO_MODE"),
        seed_demo_data=_env_flag("DRB_V2_SEED_DEMO_DATA"),
        auto_preview_on_start=_env_flag("DRB_V2_AUTO_PREVIEW_ON_START"),
        record_results_default=_env_flag("DRB_V2_RECORD_RESULTS"),
        artifact_root_dir=os.environ.get("DRB_V2_ARTIFACT_ROOT_DIR", _default_artifact_root_dir()),
        use_legacy_ocr_runtime=_env_flag("DRB_V2_USE_LEGACY_OCR_RUNTIME"),
        ocr_runtime_dir=os.environ.get("DRB_V2_OCR_RUNTIME_DIR"),
        repository_backend=repository_backend,
        database_settings=DatabaseSettings(
            host=os.environ.get("DRB_V2_DB_HOST", "localhost"),
            port=int(os.environ.get("DRB_V2_DB_PORT", "3306")),
            user=os.environ.get("DRB_V2_DB_USER", "drb"),
            password=os.environ.get("DRB_V2_DB_PASSWORD", "drb123456"),
            database=os.environ.get("DRB_V2_DB_NAME", "drb_text"),
            autocommit=_env_flag("DRB_V2_DB_AUTOCOMMIT"),
        ),
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
            ip=os.environ.get("DRB_V2_PLC_IP", str(legacy_defaults.get("plc_ip", "192.168.0.250"))),
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
