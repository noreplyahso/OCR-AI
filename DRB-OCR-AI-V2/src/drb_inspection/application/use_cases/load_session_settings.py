from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import SessionSettingsResult


@dataclass
class LoadSessionSettingsUseCase:
    repository: RepositoryAdapter

    def execute(self) -> SessionSettingsResult:
        session = self.repository.get_session()
        self.repository.record_event("Load session settings")
        return SessionSettingsResult(session=session)
