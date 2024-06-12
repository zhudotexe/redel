import logging
from abc import abstractmethod
from typing import Annotated

from kani import AIParam, ChatRole, ai_function
from rapidfuzz import fuzz

from redel.base_kani import BaseKani
from redel.state import RunState

log = logging.getLogger(__name__)


class Delegate1Mixin(BaseKani):
    @abstractmethod
    async def create_delegate_kani(self) -> BaseKani:
        raise NotImplementedError

    @ai_function()
    async def delegate(
        self,
        instructions: Annotated[str, AIParam("Detailed instructions on what your helper should do to help you.")],
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        Do not simply repeat what the user said as instructions.
        You can call this multiple times to take multiple actions; for example, you might break up a complex user query
        into multiple steps.
        NOTE: Helpers cannot see previous parts of your conversation.
        """
        log.info(f"Delegated with instructions: {instructions}")
        # if the instructions are >80% the same as the current goal, bonk
        if self.last_user_message and fuzz.ratio(instructions, self.last_user_message.content) > 80:
            return (
                "You shouldn't delegate the entire task to a helper. Handle it yourself, or if it's still too complex,"
                " try breaking it up into smaller steps and call this again."
            )

        # wait for child
        helper = await self.create_delegate_kani()
        with self.run_state(RunState.WAITING):
            result = []
            async for stream in helper.full_round_stream(instructions):
                msg = await stream.message()
                log.info(msg)
                if msg.role == ChatRole.ASSISTANT and msg.content:
                    result.append(msg.content)
            await helper.cleanup()
            return "\n".join(result)
