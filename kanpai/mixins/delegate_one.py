import logging
from abc import abstractmethod
from typing import Annotated

from kani import AIParam, ai_function
from rapidfuzz import fuzz

from kanpai.base_kani import BaseKani

log = logging.getLogger(__name__)


class Delegate1Mixin(BaseKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = None

    @abstractmethod
    def create_delegate_kani(self):
        raise NotImplementedError

    @ai_function()
    async def delegate(
        self,
        instructions: Annotated[str, AIParam("Detailed instructions on what your helper should do to help you.")],
        new: Annotated[
            bool, AIParam("Continue the conversation with the same helper (false) or ask a new helper (true).")
        ] = False,
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        You can call this multiple times to take multiple actions; for example, you might break up a complex user query
        into multiple steps.
        """
        log.info(f"Delegated with instructions: {instructions}")
        # if the instructions are >95% the same as the current goal, bonk
        if self.last_user_message and fuzz.ratio(instructions, self.last_user_message.content) > 95:
            return (
                "You shouldn't delegate the entire task to a helper. Try breaking it up into smaller steps and call"
                " this again."
            )
        # set up the helper
        if new and self.helper is not None and self.helper.context:
            # close an existing helper's browser context
            await self.helper.context.close()
        if self.helper is None or new:
            self.helper = self.create_delegate_kani()

        result = []
        async for msg in self.helper.full_round(instructions):
            log.info(msg)
            if msg.content:
                result.append(msg.content)
        return "\n".join(result)
