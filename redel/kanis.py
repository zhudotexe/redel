import asyncio
import datetime
import inspect
import logging

from kani import AIFunction, ChatMessage

from .base_kani import BaseKani
from .delegation import DelegationBase
from .namer import Namer
from .tool_config import ToolConfigType
from .tools import ToolBase

log = logging.getLogger(__name__)

# ==== prompts ====
DEFAULT_ROOT_PROMPT = (
    "# Goals\n\nYour goal is to answer the user's questions and help them out by performing actions. While you may be"
    " able to answer many questions from memory alone, the user's queries will sometimes require you to take actions."
    " You can use the provided function to ask your capable helpers, who can help you take actions.\nThe current time"
    " is {time}."
)

DEFAULT_DELEGATE_PROMPT = (
    "You are {name}, a helpful assistant with the goal of answering the user's questions as precisely as possible and"
    " helping them out by performing actions.\nYou can use the provided functions to take actions yourself or break"
    " queries up into smaller pieces and ask your capable helpers, who can help you.\nIf the user's query involves"
    " multiple steps, you should break it up into smaller pieces and delegate those pieces - for example, if you need"
    " to look up multiple sites, delegate each search to a helper. Say your plan before you do. If those pieces can be"
    " resolved at the same time, delegate them all at once. You may do multiple rounds of delegating for additional"
    " steps that depend on earlier steps.\nThe current time is {time}."
)


def get_system_prompt(kani: "BaseKani") -> str:
    """Fill in the system prompt template from the kani."""
    now = datetime.datetime.now().strftime("%a %d %b %Y, %I:%M%p")
    return kani.system_prompt.format(name=kani.name, time=now)


# ==== implementation ====
class ReDelKani(BaseKani):
    """Base class for recursive delegation kanis. Extends :class:`.BaseKani`.

    This class should not be constructed manually - it is tightly coupled to and managed by the application. You can
    get a reference to a kani powering an agent in a tool by using :attr:`.ToolBase.kani`.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("retry_attempts", 10)
        super().__init__(*args, **kwargs)
        self.namer = Namer()
        self.delegator = None
        self.tools = []

    def _register_tools(self, delegator: DelegationBase | None, tools: list[ToolBase]):
        """Overwrite this kani's functions with the functions provided by the given delegation scheme and tools.

        Should be called only once, immediately after __init__.
        """
        new_functions = {}
        # find all registered ai_functions in the delegation scheme and tools and save them
        self.delegator = delegator
        if delegator:
            new_functions.update(get_tool_functions(delegator))
        self.tools = tools
        for inst in tools:
            new_functions.update(get_tool_functions(inst))
        self.functions = new_functions

    def get_tool(self, cls: type[ToolBase]) -> ToolBase | None:
        """Get the tool from this kani's list of tools, or None if this kani does not have the given tool class."""
        return next((t for t in self.tools if type(t) is cls), None)

    async def create_delegate_kani(self, instructions: str):
        # create the new instance
        name = self.namer.get_name()
        kani_inst = ReDelKani(
            self.app.delegate_engine,
            # app args
            app=self.app,
            parent=self,
            name=name,
            dispatch_creation=False,
            # kani args
            system_prompt=self.app.delegate_system_prompt,
            **self.app.delegate_kani_kwargs,
        )

        # set up tools
        # delegation
        if self.app.delegation_scheme is None or self.depth == self.app.max_delegation_depth:
            delegation_scheme_inst = None
        else:
            delegation_scheme_inst = self.app.delegation_scheme(app=self.app, kani=kani_inst)
        # tools, TODO with the retrieved functions to use
        tool_insts = []
        for t, config in self.app.tool_configs.items():
            if config.get("always_include", False):
                tool_insts.append(t(app=self.app, kani=kani_inst, **config.get("kwargs", {})))

        # noinspection PyProtectedMember
        kani_inst._register_tools(delegator=delegation_scheme_inst, tools=tool_insts)
        if delegation_scheme_inst:
            await delegation_scheme_inst.setup()
        await asyncio.gather(*(t.setup() for t in tool_insts))
        self.app.on_kani_creation(kani_inst)
        return kani_inst

    # overrides
    async def get_prompt(self) -> list[ChatMessage]:
        # if we have a system prompt, update it with any time/name templates
        if self.system_prompt is not None:
            self.always_included_messages[0] = ChatMessage.system(get_system_prompt(self))
        return await super().get_prompt()

    async def cleanup(self):
        if self.delegator:
            await self.delegator.cleanup()
        await asyncio.gather(*(t.cleanup() for t in self.tools))
        await super().cleanup()

    async def close(self):
        if self.delegator:
            await self.delegator.close()
        await asyncio.gather(*(t.close() for t in self.tools))
        await super().close()


async def create_root_kani(
    *args,
    app,
    delegation_scheme: type[DelegationBase] | None,
    tool_configs: ToolConfigType,
    root_has_tools: bool,
    **kwargs,
) -> ReDelKani:
    """Create the root kani for the kani delegation tree."""
    kani_inst = ReDelKani(*args, app=app, dispatch_creation=False, **kwargs)
    # delegation
    if delegation_scheme:
        delegation_scheme_inst = delegation_scheme(app=app, kani=kani_inst)
    else:
        delegation_scheme_inst = None
    # tools
    tool_insts = []
    for t, config in tool_configs.items():
        if config.get("always_include_root", False) or (config.get("always_include", False) and root_has_tools):
            tool_insts.append(t(app=app, kani=kani_inst, **config.get("kwargs", {})))

    # noinspection PyProtectedMember
    kani_inst._register_tools(delegator=delegation_scheme_inst, tools=tool_insts)
    if delegation_scheme_inst:
        await delegation_scheme_inst.setup()
    await asyncio.gather(*(t.setup() for t in tool_insts))
    app.on_kani_creation(kani_inst)
    return kani_inst


def get_tool_functions(inst: ToolBase) -> dict[str, AIFunction]:
    functions = {}
    for name, member in inspect.getmembers(inst, predicate=inspect.ismethod):
        if not hasattr(member, "__ai_function__"):
            continue
        f = AIFunction(member, **member.__ai_function__)
        if f.name in functions:
            raise ValueError(f"AIFunction {f.name!r} is already registered!")
        functions[f.name] = f
    return functions
