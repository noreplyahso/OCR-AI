from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import SessionSettingsResult


@dataclass
class LogoutUserUseCase:
    repository: RepositoryAdapter

    def execute(self) -> SessionSettingsResult:
        session = self.repository.update_session(user_name="")
        self.repository.record_event("Logout current user")
        return SessionSettingsResult(session=session)
