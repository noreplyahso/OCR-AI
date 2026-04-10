from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.client import PlcClient
from drb_inspection.adapters.plc.models import PlcConnectionSettings


@dataclass
class ProtocolPlcAdapter(PlcAdapter):
    connection_settings: PlcConnectionSettings
    client: PlcClient = field(default_factory=PlcClient)
    last_error: str = ""

    def connect(self) -> bool:
        try:
            connected = self.client.connect(self.connection_settings)
        except Exception as exc:
            self.last_error = str(exc)
            return False
        if not connected:
            self.last_error = "PLC connection failed."
        return connected

    def disconnect(self) -> None:
        self.client.disconnect()

    def is_connected(self) -> bool:
        return self.client.is_connected()

    def send_result(self, result: str) -> None:
        normalized = str(result).upper()
        if not self.is_connected() and not self.connect():
            self.sent_results.append(normalized)
            return

        if normalized == "OK":
            self.client.write_light(True)
        else:
            self.client.pulse_error()
        self.sent_results.append(normalized)

    def last_result(self) -> str:
        return self.sent_results[-1] if self.sent_results else ""
