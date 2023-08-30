import abc

from kani import ChatMessage
from pydantic import BaseModel


class BaseEvent(BaseModel, abc.ABC):
    type: str


class KaniSpawn(BaseEvent):
    type: str = "kani_spawn"
    id: str
    parent: str | None
    always_included_messages: list[ChatMessage]
    chat_history: list[ChatMessage]
