from __future__ import annotations

from dataclasses import dataclass, field

from drb_inspection.adapters.plc.base import PlcAdapter
from drb_inspection.adapters.plc.models import PlcReadState
from drb_inspection.application.use_cases.poll_plc_signals import PollPlcSignalsUseCase
from drb_inspection.application.contracts.inspection import (
    InspectionCycleResult,
    InspectionRunResult,
    TaskStatus,
)


@dataclass
class FakeRunCurrentProductCycle:
    calls: int = 0

    def execute(self, **kwargs) -> InspectionCycleResult:
        self.calls += 1
        return InspectionCycleResult(
            image_ref=None,
            inspection=InspectionRunResult(
                recipe_name="fake",
                overall_status=TaskStatus.PASS,
                task_results=[],
                message="cycle ok",
            ),
            plc_result_sent="OK",
            trigger_source=str(kwargs.get("trigger_source") or "manual"),
            signal_summary=str(kwargs.get("signal_summary") or ""),
        )


@dataclass
class FakePlcAdapter(PlcAdapter):
    read_states: list[PlcReadState] = field(default_factory=list)
    light_calls: list[bool] = field(default_factory=list)

    def read_inputs_once(self) -> PlcReadState:
        if self.read_states:
            return self.read_states.pop(0)
        return PlcReadState()

    def set_light(self, enabled: bool) -> bool:
        self.light_calls.append(enabled)
        return True


def test_poll_plc_signals_triggers_cycle_on_grab_rising_edge() -> None:
    plc = FakePlcAdapter(
        connected=True,
        read_states=[
            PlcReadState(grab_requested=True),
            PlcReadState(grab_requested=True),
        ],
    )
    run_cycle = FakeRunCurrentProductCycle()
    use_case = PollPlcSignalsUseCase(plc=plc, run_current_product_cycle=run_cycle)

    first = use_case.execute()
    second = use_case.execute()

    assert first.action == "grab"
    assert first.cycle_result is not None
    assert first.cycle_result.trigger_source == "plc_grab"
    assert first.cycle_result.signal_summary == "PLC signals: grab=1 stop=0 start=0"
    assert run_cycle.calls == 1
    assert second.action == "idle"


def test_poll_plc_signals_reports_start_and_stop_edges_without_running_cycle() -> None:
    plc = FakePlcAdapter(
        connected=True,
        read_states=[
            PlcReadState(start_requested=True),
            PlcReadState(stop_requested=True),
        ],
    )
    run_cycle = FakeRunCurrentProductCycle()
    use_case = PollPlcSignalsUseCase(plc=plc, run_current_product_cycle=run_cycle)

    start_result = use_case.execute()
    stop_result = use_case.execute()

    assert start_result.action == "start"
    assert stop_result.action == "stop"
    assert run_cycle.calls == 0
    assert plc.light_calls == [True, False]


def test_poll_plc_signals_can_ignore_grab_when_cycle_trigger_is_disabled() -> None:
    plc = FakePlcAdapter(
        connected=True,
        read_states=[PlcReadState(grab_requested=True)],
    )
    run_cycle = FakeRunCurrentProductCycle()
    use_case = PollPlcSignalsUseCase(plc=plc, run_current_product_cycle=run_cycle)

    result = use_case.execute(trigger_cycle=False)

    assert result.action == "grab"
    assert result.cycle_triggered is False
    assert result.cycle_result is None
    assert run_cycle.calls == 0
