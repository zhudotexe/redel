import itertools
import json
import uuid
from typing import Iterable, TYPE_CHECKING, TypeVar

from kani import Kani

if TYPE_CHECKING:
    from .base_kani import BaseKani

T = TypeVar("T")


def create_kani_id() -> str:
    """Create a unique identifier for a kani."""
    return str(uuid.uuid4())


# ===== title =====
# thin class for typing
class AutogenerateTitle:
    """
    A sentinel class to tell ReDel to automatically generate a session title.

    Do not construct manually - use the singleton ``redel.AUTOGENERATE_TITLE``.
    """

    def __repr__(self):
        return "<AUTOGENERATE_TITLE>"


AUTOGENERATE_TITLE = AutogenerateTitle()


async def generate_conversation_title(ai: "BaseKani"):
    """Given an kani, create a title for its current conversation state."""
    helper = Kani(ai.engine)
    chat_history = "\n".join(f"{msg.role.value}: {msg.text}" for msg in ai.chat_history if msg.text)
    title = await helper.chat_round_str(
        "Here is the start of a conversation:\n"
        f"{chat_history}\n\n"
        "Come up with a short (~5 words), descriptive title for this conversation.\n\nReply with your answer only and"
        " be specific."
    )
    return title.strip(' "')


def batched(iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


def read_jsonl(fp) -> Iterable[dict]:
    """
    Yield JSON objects from the JSONL file at the given path.

    .. note::
        This function returns an iterator, not a list -- to read a full JSONL file into memory, use
        ``list(read_jsonl(...))``.
    """
    with open(fp, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)
