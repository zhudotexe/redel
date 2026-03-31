import asyncio
import logging
from typing import Annotated

from kani import AIParam, ChatRole, ai_function

from redel.state import RunState
from ._base import DelegationBase

log = logging.getLogger(__name__)


class DelegateWait2(DelegationBase):
    """
    Does not immediately wait for a sub-agent after delegating a task; agents must be explicitly waited by using
    ``wait()`` instead. This lets models without the ability to perform parallel function calling spawn multiple agents
    in parallel by calling ``delegate()`` multiple times before calling ``wait()``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helpers = {}  # name -> delegate
        self.helper_futures = {}  # name -> Future[tuple[str, str]]
        self.max_depth = kwargs.get("max_depth", 3)

    @ai_function()
    async def fork(
        self,
        instructions: Annotated[
            str,
            AIParam(
                "Detailed instructions on what your helper should do to help you. This should include all the"
                " information the helper needs."
            ),
        ],
    ):
        """
        Delegate a subtask to a helper agent. Use join(id) to get a helper's result. \
        You can call this multiple times to take multiple actions. Do not delegate the entire task you were given. \
        If the user's query can be resolved in parallel, call this multiple times then use join("all").
        """
        if self.kani.depth >= self.max_depth:
            return "Cannot fork; maximum fork depth reached"

        log.info(f"Delegated with instructions: {instructions}")

        # find or set up the helper
        helper = await self.create_delegate_kani(instructions)
        self.helpers[helper.name] = helper

        async def _task():
            try:
                result = []
                async for stream in helper.full_round_stream(instructions):
                    msg = await stream.message()
                    log.info(f"{helper.name}-{helper.depth}: {msg}")
                    if msg.role == ChatRole.ASSISTANT and msg.text:
                        result.append(msg.text)
                await helper.cleanup()
                return "\n".join(result), helper.name
            except Exception as e:
                log.exception(f"{helper.name}-{helper.depth} encountered an exception!")
                return f"encountered an exception: {e}", helper.name

        self.helper_futures[helper.name] = asyncio.create_task(_task())
        return {
            "id": helper.name,
            "status": "running",
            "task": instructions if len(instructions) < 50 else f"{instructions[:50]}[...]",
        }

    @ai_function()
    async def join(
        self,
        id: Annotated[
            str,
            AIParam('The id of the subagent. Pass "next" for the next helper, or "all" for all running subagents.'),
        ],
    ):
        """
        Wait for spawned helper agents to complete and retrieve their results. \
        Pass the agent IDs returned by `fork`, "all", or "next". \
        Returns the final responses from each agent.
        """
        if not id:
            raise ValueError("Expected 'id' argument to be a string, 'next', or 'all'.")

        if id not in self.helper_futures and id not in ("next", "all"):
            return 'The "id" param must be the name of a running helper, "next", or "all".'

        if not self.helper_futures:
            raise ValueError("There are no running subagents to join.")

        if id == "next":
            with self.kani.run_state(RunState.WAITING):
                done, _ = await asyncio.wait(self.helper_futures.values(), return_when=asyncio.FIRST_COMPLETED)
            future = done.pop()
            # prompt with name
            result, helper_name = future.result()
            # cleanup from task list
            self.helper_futures.pop(helper_name)
            return {"id": helper_name, "result": result}
        elif id == "all":
            with self.kani.run_state(RunState.WAITING):
                done, _ = await asyncio.wait(self.helper_futures.values(), return_when=asyncio.ALL_COMPLETED)
            # prompt with name
            results = []
            for future in done:
                result, helper_name = future.result()
                results.append({"id": helper_name, "result": result})
            # cleanup from task list
            self.helper_futures.clear()
            return results
        else:
            future = self.helper_futures.pop(id)
            with self.kani.run_state(RunState.WAITING):
                result, _ = await future
            return {"id": id, "result": result}
