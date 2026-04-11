from __future__ import annotations

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.adapters.db.models import DatabaseSettings, RepositoryBackend
from drb_inspection.adapters.db.mysql import MySqlRepositoryAdapter


def build_repository(
    backend: RepositoryBackend,
    database_settings: DatabaseSettings | None = None,
) -> RepositoryAdapter:
    if backend == RepositoryBackend.MYSQL:
        return MySqlRepositoryAdapter(settings=database_settings or DatabaseSettings())
    return RepositoryAdapter()
