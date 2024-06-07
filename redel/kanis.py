import datetime
import logging

from kani import ChatMessage

from .base_kani import BaseKani
from .namer import Namer
from .tool_config import ToolConfigType, get_always_included_types, get_tool_cls_kwargs

log = logging.getLogger(__name__)

# ==== prompts ====
ROOT_KANPAI = (
    "# Goals\n\nYour goal is to answer the user's questions and help them out by performing actions."
    " While you may be able to answer many questions from memory alone, the user's queries will sometimes require you"
    " to search on the Internet or take actions. You can use the provided function to ask your capable helpers, who can"
    " help you search the Internet and take actions. You should include any links they used in your response.\nThe"
    " current time is {time}."
)

DELEGATE_KANPAI = (
    "You are {name}, a helpful assistant with the goal of answering the user's questions as precisely as possible and"
    " helping them out by performing actions.\nYou can use the provided functions to search the Internet or ask your"
    " capable helpers, who can help you take actions.\nIf the user's query involves multiple steps, you should break it"
    " up into smaller pieces and delegate those pieces - for example, if you need to look up multiple sites, delegate"
    " each search to a helper. Say your plan before you do. If those pieces can be resolved at the same time, delegate"
    ' them all at once and use wait("all"). You may do multiple rounds of delegating and waiting for additional steps'
    " that depend on earlier steps.\nYou should include any links you used in your response.\nThe current time is"
    " {time}."
)


def get_system_prompt(kani: "BaseKani") -> str:
    """Fill in the system prompt template from the kani."""
    now = datetime.datetime.now().strftime("%a %d %b %Y, %I:%M%p")
    return kani.system_prompt.format(name=kani.name, time=now)


# ==== implementation ====
class ReDelBase(BaseKani):
    """Base class for recursive delegation kanis.

    This class should not be constructed manually - it is tightly coupled to and managed by the application.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("retry_attempts", 10)
        super().__init__(*args, **kwargs)
        self.namer = Namer()

    async def get_prompt(self) -> list[ChatMessage]:
        if self.system_prompt is not None:
            self.always_included_messages[0] = ChatMessage.system(get_system_prompt(self))
        return await super().get_prompt()

    # noinspection PyPep8Naming
    async def create_delegate_kani(self):
        # construct the type for the new delegate, TODO with the retrieved functions to use
        always_included_mixins = get_always_included_types(self.app.tool_configs)
        if self.depth == self.app.max_delegation_depth:
            DelegateKani = type("DelegateKani", (*always_included_mixins, ReDelBase), {})
        else:
            DelegateKani = type("DelegateKani", (*always_included_mixins, ReDelBase, self.app.delegation_scheme), {})

        # then create an instance of that type
        name = self.namer.get_name()
        return DelegateKani(
            self.app.delegate_engine,
            # app args
            app=self.app,
            parent=self,
            name=name,
            # kani args
            system_prompt=self.app.delegate_system_prompt,
            **self.app.delegate_kani_kwargs,
            # tool args
            **get_tool_cls_kwargs(self.app.tool_configs, DelegateKani.__bases__),
        )


def create_root_kani(
    *args, delegation_scheme: type | None, tool_configs: ToolConfigType, root_has_tools: bool, **kwargs
) -> ReDelBase:
    """Create the root kani for the kani delegation tree."""
    bases = (ReDelBase, delegation_scheme) if delegation_scheme is not None else (ReDelBase,)
    always_included_mixins = get_always_included_types(tool_configs)
    if root_has_tools:
        t = type("RootKani", (*always_included_mixins, *bases), {})
    else:
        t = type("RootKani", bases, {})
    return t(*args, **kwargs, **get_tool_cls_kwargs(tool_configs, t.__bases__))
