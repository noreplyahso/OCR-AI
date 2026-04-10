from __future__ import annotations

import time
from dataclasses import dataclass

from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType, PlcReadState
from drb_inspection.adapters.plc.protocols import (
    PLCProtocol,
    ModbusRTUProtocol,
    ModbusTCPProtocol,
    SLMPProtocol,
)


@dataclass
class PlcClient:
    protocol: PLCProtocol | None = None
    settings: PlcConnectionSettings | None = None

    def connect(self, settings: PlcConnectionSettings) -> bool:
        self.disconnect()
        self.settings = settings
        protocol_type = settings.protocol_type
        if protocol_type == PlcProtocolType.MODBUS_TCP:
            self.protocol = ModbusTCPProtocol()
        elif protocol_type == PlcProtocolType.MODBUS_RTU:
            self.protocol = ModbusRTUProtocol()
        elif protocol_type == PlcProtocolType.SLMP:
            self.protocol = SLMPProtocol()
        else:
            raise ValueError(f"Unsupported PLC protocol: {settings.protocol_type}")

        attempts = max(settings.tries, 1)
        for _ in range(attempts):
            kwargs = self._to_kwargs(settings)
            if self.protocol.connect(**kwargs):
                return True
            time.sleep(0.005)
        return False

    def disconnect(self) -> None:
        if self.protocol is not None:
            self.protocol.disconnect()
        self.protocol = None

    def is_connected(self) -> bool:
        return bool(self.protocol is not None and self.protocol.is_connected())

    def read_inputs_once(self) -> PlcReadState:
        if not self.is_connected():
            return PlcReadState()

        signal_map = self.settings.signal_map if self.settings is not None else None
        base_address = signal_map.grab_address if signal_map is not None else 0
        result = self.protocol.read_coils(address=base_address, count=3)
        if result is None or result.isError():
            return PlcReadState()

        bits = list(result.bits) + [False, False, False]
        return PlcReadState(
            grab_requested=bool(bits[0]),
            stop_requested=bool(bits[1]),
            start_requested=bool(bits[2]),
        )

    def write_light(self, enabled: bool) -> bool:
        address = self.settings.signal_map.light_address if self.settings is not None else 100
        return self._write_coil(address=address, value=enabled)

    def pulse_error(self, pulse_seconds: float = 0.5) -> bool:
        address = self.settings.signal_map.error_address if self.settings is not None else 101
        if not self._write_coil(address=address, value=True):
            return False
        time.sleep(pulse_seconds)
        return self._write_coil(address=address, value=False)

    def _write_coil(self, address: int, value: bool) -> bool:
        if not self.is_connected():
            return False
        result = self.protocol.write_coil(address=address, value=value)
        return bool(result is not None and not result.isError())

    def _to_kwargs(self, settings: PlcConnectionSettings) -> dict:
        protocol_type = settings.protocol_type
        if protocol_type == PlcProtocolType.MODBUS_TCP:
            return {"ip": settings.ip, "port": settings.port}
        if protocol_type == PlcProtocolType.MODBUS_RTU:
            return {
                "port": settings.serial_port,
                "baudrate": settings.baudrate,
                "parity": settings.parity,
                "stopbits": settings.stopbits,
                "bytesize": settings.bytesize,
                "slave_id": settings.slave_id,
            }
        return {
            "ip": settings.ip,
            "port": settings.port,
            "plc_type": settings.plc_type,
            "comm_type": settings.comm_type,
        }
