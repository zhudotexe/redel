import logging
from typing import Annotated

from kani import AIParam, ai_function

from .mixins.browsing import BrowsingKani
from .prompts import ROOT_KANPAI

log = logging.getLogger(__name__)


class Kanpai(BrowsingKani):
    # delegation
    @ai_function()
    async def delegate(
        self, instructions: Annotated[str, AIParam("Detailed instructions on what your helper should do to help you.")]
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        You can call this multiple times to take multiple actions; for example, you might break up a complex user query
        into multiple steps.
        """
        log.info(f"Delegated with instructions: {instructions}")
        helper = Kanpai(self.engine, browser=self.browser, system_prompt=ROOT_KANPAI)
        result = []
        async for msg in helper.full_round(instructions):
            log.info(msg)
            if msg.content:
                result.append(msg.content)
        # close the sub-helper's browser context
        if helper.context:
            await helper.context.close()
        return "\n".join(result)
