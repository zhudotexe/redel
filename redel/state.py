import enum

from kani import ChatMessage
from pydantic import BaseModel


class RunState(enum.Enum):
    STOPPED = "stopped"  # not currently running anything or waiting on a child
    RUNNING = "running"  # gpt-4 is generating something
    WAITING = "waiting"  # waiting on a child
    ERRORED = "errored"  # panic


class KaniState(BaseModel):
    id: str
    depth: int
    parent: str | None
    children: list[str]
    always_included_messages: list[ChatMessage]
    chat_history: list[ChatMessage]
    state: RunState
    name: str
