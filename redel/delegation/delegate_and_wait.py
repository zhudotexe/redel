import asyncio
import logging
from typing import Annotated

from kani import AIParam, ChatRole, ai_function
from rapidfuzz import fuzz

from redel.state import RunState
from ._base import DelegationBase

log = logging.getLogger(__name__)


class DelegateWait(DelegationBase):
    """
    Does not immediately wait for a sub-agent after delegating a task; agents must be explicitly waited by using
    ``wait()`` instead. This lets models without the ability to perform parallel function calling spawn multiple agents
    in parallel by calling ``delegate()`` multiple times before calling ``wait()``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helpers = {}  # name -> delegate
        self.helper_futures = {}  # name -> Future[tuple[str, str]]

    @ai_function()
    async def delegate(
        self,
        instructions: Annotated[
            str,
            AIParam(
                "Detailed instructions on what your helper should do to help you. This should include all the"
                " information the helper needs."
            ),
        ],
        who: Annotated[
            str,
            AIParam("If you need to ask a previous helper a follow-up, pass their name here; otherwise omit."),
        ] = None,
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        Use wait() to get a helper's result.
        You can call this multiple times to take multiple actions.
        You should break up user queries into multiple smaller queries if possible.
        Do not delegate the entire task you were given.
        If the user's query can be resolved in parallel, call this multiple times then use wait("all").
        """
        log.info(f"Delegated with instructions: {instructions}")
        # if the instructions are >80% the same as the current goal, bonk
        if self.kani.last_user_message and fuzz.ratio(instructions, self.kani.last_user_message.content) > 80:
            return (
                "You shouldn't delegate the entire task to a helper. Handle it yourself, or if it's still too complex,"
                " try breaking it up into smaller steps and call this again."
            )

        # find or set up the helper
        if who and who in self.helpers:
            if who in self.helper_futures:
                return (
                    f"{who!r} is currently busy. You can leave `who` empty to find a new available helper or wait on"
                    f" {who!r} and retry."
                )
            helper = self.helpers[who]
        else:
            helper = await self.create_delegate_kani(instructions)
            self.helpers[helper.name] = helper

        async def _task():
            try:
                result = []
                async for stream in helper.full_round_stream(instructions):
                    msg = await stream.message()
                    log.info(f"{helper.name}-{helper.depth}: {msg}")
                    if msg.role == ChatRole.ASSISTANT and msg.content:
                        result.append(msg.content)
                await helper.cleanup()
                return "\n".join(result), helper.name
            except Exception as e:
                log.exception(f"{helper.name}-{helper.depth} encountered an exception!")
                return f"encountered an exception: {e}", helper.name

        self.helper_futures[helper.name] = asyncio.create_task(_task())
        return f"{helper.name!r} is helping you with this request."

    @ai_function(auto_truncate=6000)
    async def wait(
        self,
        until: Annotated[
            str,
            AIParam('The name of the helper. Pass "next" for the next helper, or "all" for all running helpers.'),
        ],
    ):
        """Wait for a helper to finish their task and get their result."""
        if until not in self.helper_futures and until not in ("next", "all"):
            return 'The "until" param must be the name of a running helper, "next", or "all".'

        if until == "next":
            with self.kani.run_state(RunState.WAITING):
                done, _ = await asyncio.wait(self.helper_futures.values(), return_when=asyncio.FIRST_COMPLETED)
            future = done.pop()
            # prompt with name
            result, helper_name = future.result()
            # cleanup from task list
            self.helper_futures.pop(helper_name)
            return f"{helper_name}:\n{result}"
        elif until == "all":
            with self.kani.run_state(RunState.WAITING):
                done, _ = await asyncio.wait(self.helper_futures.values(), return_when=asyncio.ALL_COMPLETED)
            # prompt with name
            results = []
            for future in done:
                result, helper_name = future.result()
                results.append(f"{helper_name}:\n{result}")
            # cleanup from task list
            self.helper_futures.clear()
            return "\n\n=====\n\n".join(results)
        else:
            future = self.helper_futures.pop(until)
            with self.kani.run_state(RunState.WAITING):
                result, _ = await future
            return f"{until}:\n{result}"
