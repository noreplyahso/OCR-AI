from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.plc.models import (
    PlcConnectionSettings,
    PlcProtocolType,
    PlcReadState,
    PlcVendor,
)
from drb_inspection.adapters.plc.profiles import resolve_signal_map


@dataclass
class PlcAdapter:
    connection_settings: PlcConnectionSettings = field(
        default_factory=lambda: PlcConnectionSettings(
            vendor=PlcVendor.DEMO,
            protocol_type=PlcProtocolType.DEMO,
            signal_map=resolve_signal_map(PlcVendor.DEMO),
        )
    )
    sent_results: list[str] = field(default_factory=list)
    connected: bool = True

    def connect(self) -> bool:
        self.connected = True
        return self.connected

    def disconnect(self) -> None:
        self.connected = False

    def send_result(self, result: str) -> None:
        self.sent_results.append(result)

    def is_connected(self) -> bool:
        return self.connected

    def read_inputs_once(self) -> PlcReadState:
        return PlcReadState()

    def set_light(self, enabled: bool) -> bool:
        return self.connected

    def pulse_error(self, pulse_seconds: float = 0.5) -> bool:
        return self.connected

    def last_result(self) -> str:
        return self.sent_results[-1] if self.sent_results else ""
