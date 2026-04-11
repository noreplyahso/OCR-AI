from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import SessionSettingsResult


@dataclass
class MoveSessionRoiUseCase:
    repository: RepositoryAdapter

    def execute(
        self,
        *,
        direction: str,
        roi_index: int | None = None,
        move_all: bool = False,
        step: int = 10,
    ) -> SessionSettingsResult:
        normalized_direction = direction.strip().lower()
        if normalized_direction not in {"left", "right", "up", "down"}:
            raise ValueError(f"Unsupported ROI move direction: {direction}")
        if step <= 0:
            raise ValueError("ROI move step must be positive")

        targets = self._resolve_targets(roi_index=roi_index, move_all=move_all)
        delta_x, delta_y = self._resolve_delta(normalized_direction, step)
        session = self.repository.get_session()

        updates: dict[str, int] = {}
        for index in targets:
            x_value = getattr(session, f"roi_x{index}")
            y_value = getattr(session, f"roi_y{index}")
            updates[f"roi_x{index}"] = x_value + delta_x
            updates[f"roi_y{index}"] = y_value + delta_y

        updated_session = self.repository.update_session(**updates)
        self.repository.record_event(
            "Move session ROI"
            f" direction={normalized_direction}"
            f" targets={targets}"
            f" step={step}"
        )
        return SessionSettingsResult(session=updated_session)

    def _resolve_targets(self, *, roi_index: int | None, move_all: bool) -> list[int]:
        if move_all:
            return [1, 2, 3, 4, 5]
        if roi_index not in {1, 2, 3, 4, 5}:
            raise ValueError("ROI index must be between 1 and 5 when move_all is disabled")
        return [roi_index]

    def _resolve_delta(self, direction: str, step: int) -> tuple[int, int]:
        if direction == "left":
            return (-step, 0)
        if direction == "right":
            return (step, 0)
        if direction == "up":
            return (0, -step)
        return (0, step)
