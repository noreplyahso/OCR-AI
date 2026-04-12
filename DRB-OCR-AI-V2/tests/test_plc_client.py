from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.plc.client import PlcClient
from drb_inspection.adapters.plc.models import PlcConnectionSettings, PlcProtocolType, PlcReadState


@dataclass
class _FakeReadResult:
    bits: list[bool]
    error: bool = False

    def isError(self) -> bool:
        return self.error


@dataclass
class _FakeWriteResult:
    error: bool = False

    def isError(self) -> bool:
        return self.error


@dataclass
class _FakeProtocol:
    connected: bool = True
    writes: list[tuple[int, bool]] = field(default_factory=list)
    bits: list[bool] = field(default_factory=lambda: [True, False, True])
    connect_kwargs: dict | None = None

    def connect(self, **kwargs) -> bool:
        self.connect_kwargs = kwargs
        self.connected = True
        return True

    def disconnect(self) -> None:
        self.connected = False

    def read_coils(self, address: int, count: int):
        return _FakeReadResult(bits=self.bits[:count], error=False)

    def write_coil(self, address: int, value: bool):
        self.writes.append((address, value))
        return _FakeWriteResult(error=False)

    def is_connected(self) -> bool:
        return self.connected


def test_plc_client_reads_input_state_from_protocol() -> None:
    client = PlcClient(protocol=_FakeProtocol())

    state = client.read_inputs_once()

    assert isinstance(state, PlcReadState)
    assert state.grab_requested is True
    assert state.stop_requested is False
    assert state.start_requested is True


def test_plc_client_pulses_error_bit() -> None:
    protocol = _FakeProtocol()
    client = PlcClient(protocol=protocol)

    result = client.pulse_error(pulse_seconds=0)

    assert result is True
    assert protocol.writes == [(101, True), (101, False)]


def test_plc_client_connect_uses_legacy_protocol_factory(monkeypatch) -> None:
    protocol = _FakeProtocol(connected=False)
    client = PlcClient()
    settings = PlcConnectionSettings(
        protocol_type=PlcProtocolType.SLMP,
        ip="192.168.0.250",
        port=5000,
        plc_type="Q",
        comm_type="binary",
    )

    monkeypatch.setattr(
        "drb_inspection.adapters.plc.client.build_legacy_protocol",
        lambda protocol_type: protocol,
    )

    connected = client.connect(settings)

    assert connected is True
    assert client.protocol is protocol
    assert protocol.connect_kwargs == {
        "ip": "192.168.0.250",
        "port": 5000,
        "plc_type": "Q",
        "comm_type": "binary",
    }
