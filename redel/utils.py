import uuid
from typing import TYPE_CHECKING

from kani import ChatMessage, Kani

if TYPE_CHECKING:
    from .base_kani import BaseKani


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
