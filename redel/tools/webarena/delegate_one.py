import logging
from typing import Annotated

from kani import AIParam, ChatRole, ai_function
from rapidfuzz import fuzz

from redel.delegation import DelegationBase
from redel.state import RunState

log = logging.getLogger(__name__)


class WebArenaDelegate1Mixin(DelegationBase):
    """This is mostly a clone of normal Delegate1Mixin but with the following changes:
    - 20 max function rounds (up from 5)
    - delegate() prompt mentions that child can see browser
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
            async for stream in helper.full_round_stream(instructions, max_function_rounds=20):
                msg = await stream.message()
                log.info(msg)
                if msg.role == ChatRole.ASSISTANT and msg.content:
                    result.append(msg.content)
            await helper.cleanup()
            return "\n".join(result)
