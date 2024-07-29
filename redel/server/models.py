from pathlib import Path

from pydantic import BaseModel

from redel.state import KaniState


class SessionMeta(BaseModel):
    id: str
    title: str | None
    last_modified: float
    n_events: int


class SaveMeta(SessionMeta):
    grouping_prefix: list[str]
    state_fp: Path
    event_fp: Path


class SessionState(SessionMeta):
    state: list[KaniState]
