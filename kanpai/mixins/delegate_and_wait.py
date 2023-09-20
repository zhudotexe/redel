import asyncio
import itertools
import logging
from abc import abstractmethod
from typing import Annotated

from kani import AIParam, ai_function
from rapidfuzz import fuzz

from kanpai.base_kani import BaseKani

log = logging.getLogger(__name__)


class DelegateWaitMixin(BaseKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namer = Namer()
        self.helpers = {}  # name -> delegate
        self.helper_futures = {}  # name -> Future[str]

    @abstractmethod
    def create_delegate_kani(self) -> BaseKani:
        raise NotImplementedError

    @ai_function()
    async def delegate(
        self,
        instructions: Annotated[str, AIParam("Detailed instructions on what your helper should do to help you.")],
        who: Annotated[str, AIParam("Who should handle this request (leave empty for whoever is available).")] = None,
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        Use wait() to get a helper's result.
        You can call this multiple times to take multiple actions.
        You should break up user queries into multiple smaller queries if possible.
        If the user's query can be resolved in parallel, call this multiple times then use wait("all").
        """
        log.info(f"Delegated with instructions: {instructions}")
        # if the instructions are >95% the same as the current goal, bonk
        if self.last_user_message and fuzz.ratio(instructions, self.last_user_message.content) > 95:
            return (
                "You shouldn't delegate the entire task to a helper. Try breaking it up into smaller steps and call"
                " this again."
            )

        # find or set up the helper
        if who and who in self.helpers:
            if who in self.helper_futures:
                return (
                    f"{who!r} is currently busy. You can leave `who` empty to find a new available helper or wait on"
                    f" {who!r} and retry."
                )
            name = who
            helper = self.helpers[who]
        else:
            name = self.namer.get_name()
            helper = self.create_delegate_kani()
            self.helpers[name] = helper

        async def _task():
            result = []
            async for msg in helper.full_round(instructions):
                log.info(msg)
                if msg.content:
                    result.append(msg.content)
            await helper.cleanup()
            return "\n".join(result)

        self.helper_futures[name] = asyncio.create_task(_task())
        return f"{name!r} is helping you with this request."

    @ai_function()
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
            done, _ = await asyncio.wait(self.helper_futures.values(), return_when=asyncio.FIRST_COMPLETED)
            future = done.pop()
            # cleanup from task list
            helper_name = next(k for k, v in self.helper_futures.items() if v is future)
            self.helper_futures.pop(helper_name)
            # prompt with name
            result = future.result()
            return f"{helper_name}:\n{result}"
        elif until == "all":
            done, _ = await asyncio.wait(self.helper_futures.values(), return_when=asyncio.ALL_COMPLETED)
            # prompt with name
            results = []
            for helper_name, future in self.helper_futures.items():
                result = future.result()
                results.append(f"{helper_name}:\n{result}")
            # cleanup from task list
            self.helper_futures.clear()
            return "\n\n=====\n\n".join(results)
        else:
            future = self.helper_futures.pop(until)
            result = await future
            return f"{until}:\n{result}"


class Namer:
    all_names = [
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "iota",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "omicron",
        "pi",
        "rho",
        "sigma",
        "tau",
        "upsilon",
        "phi",
        "chi",
        "psi",
        "omega",
    ]

    def __init__(self):
        self.gen = itertools.cycle(self.all_names)

    def get_name(self):
        return next(self.gen)
