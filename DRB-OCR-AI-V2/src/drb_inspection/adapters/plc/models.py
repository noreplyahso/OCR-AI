from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlcVendor(str, Enum):
    DEMO = "demo"
    SIEMENS = "siemens"
    MITSUBISHI = "mitsubishi"
    DELTA = "delta"
    GENERIC = "generic"


class PlcProtocolType(str, Enum):
    DEMO = "demo"
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    SLMP = "slmp"


@dataclass(frozen=True)
class PlcSignalMap:
    grab_address: int = 0
    stop_address: int = 1
    start_address: int = 2
    light_address: int = 100
    error_address: int = 101


@dataclass(frozen=True)
class PlcConnectionSettings:
    vendor: PlcVendor = PlcVendor.DEMO
    protocol_type: PlcProtocolType = PlcProtocolType.DEMO
    ip: str = "192.168.0.250"
    port: int = 502
    tries: int = 1
    serial_port: str = "COM1"
    baudrate: int = 9600
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    slave_id: int = 1
    plc_type: str = "Q"
    comm_type: str = "binary"
    signal_map: PlcSignalMap = PlcSignalMap()


@dataclass
class PlcReadState:
    grab_requested: bool = False
    stop_requested: bool = False
    start_requested: bool = False
