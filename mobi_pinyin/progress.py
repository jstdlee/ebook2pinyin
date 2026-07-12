from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Stage:
    name: str
    current: int
    total: int
    message: str


ProgressCallback = Callable[[Stage], None]


def noop_progress(stage: Stage) -> None:
    return None
