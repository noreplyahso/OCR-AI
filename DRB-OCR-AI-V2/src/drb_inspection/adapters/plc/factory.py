from __future__ import annotations

from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType
from drb_inspection.adapters.plc.protocol_adapter import ProtocolPlcAdapter


def build_plc_adapter(connection_settings: PlcConnectionSettings | None = None):
    settings = connection_settings or PlcConnectionSettings()
    if settings.protocol_type == PlcProtocolType.DEMO:
        return PlcAdapter(connection_settings=settings)
    return ProtocolPlcAdapter(connection_settings=settings)
