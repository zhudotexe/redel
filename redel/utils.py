import itertools
import json
import uuid
from typing import Iterable, TYPE_CHECKING, TypeVar

from kani import ChatMessage, Kani

if TYPE_CHECKING:
    from .base_kani import BaseKani

T = TypeVar("T")


def create_kani_id() -> str:
    """Create a unique identifier for a kani."""
    return str(uuid.uuid4())


async def generate_conversation_title(ai: "BaseKani"):
    """Given an kani, create a title for its current conversation state."""
    helper = Kani(ai.engine, chat_history=[ChatMessage.user("Here is the start of a conversation:"), *ai.chat_history])
    title = await helper.chat_round_str(
        "Come up with a punchy title for this conversation.\n\nReply with your answer only and be specific."
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
    """Yield JSON objects from the given JSONL file."""
    with open(fp) as f:
        for line in f:
            yield json.loads(line)
