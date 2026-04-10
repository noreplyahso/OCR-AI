"""PLC adapter package."""

from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.client import PlcClient
from drb_inspection.adapters.plc.factory import build_plc_adapter
from drb_inspection.adapters.plc.models import (
    PlcConnectionSettings,
    PlcProtocolType,
    PlcReadState,
    PlcSignalMap,
    PlcVendor,
)
from drb_inspection.adapters.plc.protocol_adapter import ProtocolPlcAdapter
from drb_inspection.adapters.plc.profiles import resolve_signal_map

__all__ = [
    "PlcAdapter",
    "PlcClient",
    "PlcConnectionSettings",
    "PlcProtocolType",
    "PlcReadState",
    "PlcSignalMap",
    "PlcVendor",
    "ProtocolPlcAdapter",
    "build_plc_adapter",
    "resolve_signal_map",
]
