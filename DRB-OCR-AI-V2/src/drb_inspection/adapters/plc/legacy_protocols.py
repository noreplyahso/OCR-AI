from __future__ import annotations

from abc import ABC, abstractmethod

from drb_inspection.adapters.plc.models import PlcProtocolType


class PLCProtocol(ABC):
    """Legacy-compatible PLC protocol contract sourced from V1 PLC.py."""

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_coils(self, address: int, count: int):
        raise NotImplementedError

    @abstractmethod
    def write_coil(self, address: int, value: bool):
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        raise NotImplementedError


class ModbusTCPProtocol(PLCProtocol):
    """V1 Modbus TCP implementation."""

    COIL_OFFSET = 8192

    def __init__(self):
        self.client = None
        self._connected = False

    def connect(self, ip="192.168.0.250", port=502, **kwargs) -> bool:
        from pymodbus.client import ModbusTcpClient

        self.client = ModbusTcpClient(ip, port=port)
        self._connected = self.client.connect()
        return self._connected

    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self._connected = False

    def read_coils(self, address: int, count: int):
        if self.client:
            return self.client.read_coils(address=address + self.COIL_OFFSET, count=count)
        return None

    def write_coil(self, address: int, value: bool):
        if self.client:
            return self.client.write_coil(address=address + self.COIL_OFFSET, value=value)
        return None

    def is_connected(self) -> bool:
        return self._connected


class ModbusRTUProtocol(PLCProtocol):
    """V1 Modbus RTU implementation."""

    COIL_OFFSET = 8192

    def __init__(self):
        self.client = None
        self._connected = False
        self.slave_id = 1

    def connect(
        self,
        port="COM1",
        baudrate=9600,
        parity="N",
        stopbits=1,
        bytesize=8,
        slave_id=1,
        **kwargs,
    ) -> bool:
        from pymodbus.client import ModbusSerialClient

        self.slave_id = slave_id
        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
        )
        self._connected = self.client.connect()
        return self._connected

    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self._connected = False

    def read_coils(self, address: int, count: int):
        if self.client:
            return self.client.read_coils(address=address + self.COIL_OFFSET, count=count, slave=self.slave_id)
        return None

    def write_coil(self, address: int, value: bool):
        if self.client:
            return self.client.write_coil(address=address + self.COIL_OFFSET, value=value, slave=self.slave_id)
        return None

    def is_connected(self) -> bool:
        return self._connected


class SLMPReadResult:
    """Legacy wrapper to match V1 error/result shape."""

    def __init__(self, bits: list | None = None, error: bool = False):
        self.bits = bits or []
        self._error = error

    def isError(self) -> bool:
        return self._error


class SLMPWriteResult:
    """Legacy wrapper to match V1 error/result shape."""

    def __init__(self, error: bool = False):
        self._error = error

    def isError(self) -> bool:
        return self._error


class SLMPProtocol(PLCProtocol):
    """
    V1 Mitsubishi SLMP/MC protocol implementation.

    Supports Q/L/QnA/iQ-L/iQ-R and mirrors the behavior from lib/PLC.py.
    """

    def __init__(self):
        self.client = None
        self._connected = False

    def connect(self, ip="192.168.0.250", port=5000, plc_type="Q", comm_type="binary", **kwargs) -> bool:
        import pymcprotocol

        self.client = pymcprotocol.Type3E(plctype=plc_type)
        if comm_type == "ascii":
            self.client.setaccessopt(commtype="ascii")

        try:
            self.client.connect(ip, int(port))
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self) -> None:
        if self.client and self._connected:
            try:
                self.client.close()
            except Exception:
                pass
            self._connected = False

    def read_coils(self, address: int, count: int):
        if not self.client or not self._connected:
            return SLMPReadResult(error=True)

        try:
            values = self.client.batchread_bitunits(headdevice=f"M{address}", readsize=count)
            bits = [bool(v) for v in values]
            return SLMPReadResult(bits=bits, error=False)
        except Exception:
            return SLMPReadResult(error=True)

    def write_coil(self, address: int, value: bool):
        if not self.client or not self._connected:
            return SLMPWriteResult(error=True)

        try:
            self.client.batchwrite_bitunits(headdevice=f"M{address}", values=[1 if value else 0])
            return SLMPWriteResult(error=False)
        except Exception:
            return SLMPWriteResult(error=True)

    def is_connected(self) -> bool:
        return self._connected


def build_legacy_protocol(protocol_type: PlcProtocolType) -> PLCProtocol:
    if protocol_type == PlcProtocolType.MODBUS_TCP:
        return ModbusTCPProtocol()
    if protocol_type == PlcProtocolType.MODBUS_RTU:
        return ModbusRTUProtocol()
    if protocol_type == PlcProtocolType.SLMP:
        return SLMPProtocol()
    raise ValueError(f"Unsupported PLC protocol: {protocol_type}")
