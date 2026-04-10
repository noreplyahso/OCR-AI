from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import SessionSettingsResult


@dataclass
class SaveSessionSettingsUseCase:
    repository: RepositoryAdapter

    def execute(self, **updates) -> SessionSettingsResult:
        session = self.repository.update_session(**updates)
        self.repository.record_event(f"Save session settings keys={sorted(updates)}")
        return SessionSettingsResult(session=session)
