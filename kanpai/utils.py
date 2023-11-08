import uuid
from typing import TYPE_CHECKING

from kani import ChatRole
from kani.engines.openai.models import OpenAIChatMessage

if TYPE_CHECKING:
    from .base_kani import BaseKani


def create_kani_id() -> str:
    """Create a unique identifier for a kani."""
    return str(uuid.uuid4())


async def generate_conversation_title(ai: "BaseKani"):
    """Given an kani, create a title for its current conversation state."""
    completion = await ai.app.engine.client.create_chat_completion(
        "gpt-4",
        [
            OpenAIChatMessage(role="user", content="Here is the start of a conversation:"),
            *[OpenAIChatMessage.from_chatmessage(m) for m in ai.chat_history],
            OpenAIChatMessage(
                role="user",
                content=(
                    "Come up with a punchy title for this conversation.\n\nReply with your answer only and be specific."
                ),
            ),
        ],
    )
    return completion.message.text.strip(' "')
