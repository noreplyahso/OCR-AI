from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DomainEvent:
    name: str
    payload: dict[str, object]
