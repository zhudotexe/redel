import logging
from typing import Annotated

from kani import AIParam, ai_function

from .mixins.browsing import BrowsingKani
from .prompts import ROOT_KANPAI

log = logging.getLogger(__name__)


class Kanpai(BrowsingKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = None

    # delegation
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
        # set up the helper
        if new and self.helper is not None and self.helper.context:
            # close an existing helper's browser context
            await self.helper.context.close()
        if self.helper is None or new:
            self.helper = Kanpai(self.engine, browser=self.browser, system_prompt=ROOT_KANPAI)

        result = []
        async for msg in self.helper.full_round(instructions):
            log.info(msg)
            if msg.content:
                result.append(msg.content)
        return "\n".join(result)
