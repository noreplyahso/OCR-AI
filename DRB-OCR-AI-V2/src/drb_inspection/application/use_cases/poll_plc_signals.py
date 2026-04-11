from __future__ import annotations

import time
from dataclasses import dataclass, field

from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.models import PlcReadState
from drb_inspection.application.contracts.runtime import PlcPollResult
from drb_inspection.application.use_cases.run_current_product_cycle import RunCurrentProductCycleUseCase


@dataclass
class PollPlcSignalsUseCase:
    plc: PlcAdapter
    run_current_product_cycle: RunCurrentProductCycleUseCase
    debounce_seconds: float = 1.0
    previous_state: PlcReadState = field(default_factory=PlcReadState)
    last_grab_event_at: float = 0.0
    last_stop_event_at: float = 0.0
    last_start_event_at: float = 0.0

    def execute(self, *, trigger_cycle: bool = True, record_results: bool = False) -> PlcPollResult:
        if not self.plc.is_connected():
            try:
                connected = bool(self.plc.connect())
            except Exception as exc:
                return PlcPollResult(
                    read_state=PlcReadState(),
                    action="error",
                    signal_summary=self._build_signal_summary(PlcReadState()),
                    message=f"PLC connect failed: {exc}",
                )
            if not connected:
                return PlcPollResult(
                    read_state=PlcReadState(),
                    action="error",
                    signal_summary=self._build_signal_summary(PlcReadState()),
                    message="PLC is not connected.",
                )

        read_state = self.plc.read_inputs_once()
        signal_summary = self._build_signal_summary(read_state)
        now = time.time()

        stop_edge = self._is_rising_edge(
            current=read_state.stop_requested,
            previous=self.previous_state.stop_requested,
            now=now,
            last_event_at=self.last_stop_event_at,
        )
        start_edge = self._is_rising_edge(
            current=read_state.start_requested,
            previous=self.previous_state.start_requested,
            now=now,
            last_event_at=self.last_start_event_at,
        )
        grab_edge = self._is_rising_edge(
            current=read_state.grab_requested,
            previous=self.previous_state.grab_requested,
            now=now,
            last_event_at=self.last_grab_event_at,
        )
        self.previous_state = read_state

        if stop_edge:
            self.last_stop_event_at = now
            self.plc.set_light(False)
            return PlcPollResult(
                read_state=read_state,
                action="stop",
                signal_summary=signal_summary,
                message="PLC stop requested.",
            )

        if start_edge:
            self.last_start_event_at = now
            self.plc.set_light(True)
            return PlcPollResult(
                read_state=read_state,
                action="start",
                signal_summary=signal_summary,
                message="PLC start requested.",
            )

        if grab_edge:
            self.last_grab_event_at = now
            if not trigger_cycle:
                return PlcPollResult(
                    read_state=read_state,
                    action="grab",
                    cycle_triggered=False,
                    signal_summary=signal_summary,
                    message="PLC grab requested but inspection is disabled.",
                )
            try:
                if record_results:
                    cycle_result = self.run_current_product_cycle.execute(
                        record_results=True,
                        trigger_source="plc_grab",
                        signal_summary=signal_summary,
                    )
                else:
                    cycle_result = self.run_current_product_cycle.execute(
                        trigger_source="plc_grab",
                        signal_summary=signal_summary,
                    )
            except Exception as exc:
                return PlcPollResult(
                    read_state=read_state,
                    action="error",
                    cycle_triggered=False,
                    signal_summary=signal_summary,
                    message=f"PLC grab requested but cycle failed: {exc}",
                )
            return PlcPollResult(
                read_state=read_state,
                action="grab",
                cycle_result=cycle_result,
                cycle_triggered=True,
                signal_summary=signal_summary,
                message="PLC grab requested.",
            )

        return PlcPollResult(
            read_state=read_state,
            action="idle",
            signal_summary=signal_summary,
            message="PLC idle.",
        )

    def _is_rising_edge(
        self,
        *,
        current: bool,
        previous: bool,
        now: float,
        last_event_at: float,
    ) -> bool:
        if not current or previous:
            return False
        return (now - last_event_at) > self.debounce_seconds

    def _build_signal_summary(self, read_state: PlcReadState) -> str:
        return (
            "PLC signals:"
            f" grab={int(read_state.grab_requested)}"
            f" stop={int(read_state.stop_requested)}"
            f" start={int(read_state.start_requested)}"
        )
