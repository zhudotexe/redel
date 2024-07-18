import logging
from typing import Annotated

from kani import AIParam, ChatRole, ai_function
from rapidfuzz import fuzz

from redel.state import RunState
from ._base import DelegationBase

log = logging.getLogger(__name__)


class DelegateOne(DelegationBase):
    """
    Delegate and immediately wait for the result of the sub-agent.
    Can be called in parallel to run multiple sub-agents in parallel.
    """

    @ai_function()
    async def delegate(
        self,
        instructions: Annotated[str, AIParam("Detailed instructions on what your helper should do to help you.")],
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        Do not simply repeat what the user said as instructions.
        You should use this to break up complex user queries into multiple simpler steps.
        NOTE: Helpers cannot see previous parts of your conversation.
        """
        log.info(f"Delegated with instructions: {instructions}")
        # if the instructions are >80% the same as the current goal, bonk
        if self.kani.last_user_message and fuzz.ratio(instructions, self.kani.last_user_message.content) > 80:
            return (
                "You shouldn't delegate the entire task to a helper. Handle it yourself, or if it's still too complex,"
                " try breaking it up into smaller steps and call this again."
            )

        # wait for child
        helper = await self.create_delegate_kani(instructions)
        with self.kani.run_state(RunState.WAITING):
            result = []
            async for stream in helper.full_round_stream(instructions, max_function_rounds=5):  # TODO temp
                msg = await stream.message()
                log.info(msg)
                if msg.role == ChatRole.ASSISTANT and msg.content:
                    result.append(msg.content)
            await helper.cleanup()
            return "\n".join(result)
