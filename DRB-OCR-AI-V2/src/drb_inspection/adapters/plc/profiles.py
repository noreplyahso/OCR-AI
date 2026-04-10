from __future__ import annotations

from drb_inspection.adapters.plc.models import PlcSignalMap, PlcVendor


DEFAULT_SIGNAL_MAPS: dict[PlcVendor, PlcSignalMap] = {
    PlcVendor.DEMO: PlcSignalMap(),
    PlcVendor.GENERIC: PlcSignalMap(),
    PlcVendor.MITSUBISHI: PlcSignalMap(
        grab_address=0,
        stop_address=1,
        start_address=2,
        light_address=100,
        error_address=101,
    ),
    PlcVendor.SIEMENS: PlcSignalMap(
        grab_address=0,
        stop_address=1,
        start_address=2,
        light_address=10,
        error_address=11,
    ),
    PlcVendor.DELTA: PlcSignalMap(
        grab_address=0,
        stop_address=1,
        start_address=2,
        light_address=200,
        error_address=201,
    ),
}


def resolve_signal_map(vendor: PlcVendor) -> PlcSignalMap:
    return DEFAULT_SIGNAL_MAPS.get(vendor, PlcSignalMap())
