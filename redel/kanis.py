import datetime
import logging
from typing import Iterable, Type

from kani import ChatMessage

from .base_kani import BaseKani
from .namer import Namer

log = logging.getLogger(__name__)

# ==== prompts ====
ROOT_KANPAI = (
    "# Persona\n\nYou are acting as Kanpai. You are firm, dependable, a bit hot-headed, and tenacious, with a fiery"
    " temper. Despite being serious, you showcase a strong sense of camaraderie and loyalty. You should always reply in"
    " character.\n\n# Goals\n\nYour goal is to answer the user's questions and help them out by performing actions."
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
    """Base class for recursive delegation kanis."""

    def __init__(
        self,
        *args,
        delegation_scheme: type,
        always_included_mixins: Iterable[type] = (),
        max_delegation_depth: int = None,
        **kwargs,
    ):
        """
        :param delegation_scheme: The delegation scheme to use (Delegate1Mixin or DelegateWaitMixin).
        :param always_included_mixins: Mixins to include for each delegate (but not the root).
        :param max_delegation_depth: The maximum depth of the delegation chain - any kanis created at this depth will
            not inherit from the *delegation_scheme*.
        """
        kwargs.setdefault("retry_attempts", 10)
        super().__init__(*args, **kwargs)
        self.namer = Namer()
        self.delegation_scheme = delegation_scheme
        self.always_included_mixins = always_included_mixins
        self.max_delegation_depth = max_delegation_depth

    async def get_prompt(self) -> list[ChatMessage]:
        if self.system_prompt is not None:
            self.always_included_messages[0] = ChatMessage.system(get_system_prompt(self))
        return await super().get_prompt()

    # noinspection PyTypeChecker
    async def build_delegate_type(self) -> Type["ReDelBase"]:
        # construct the type for the new delegate, TODO with the retrieved functions to use
        if self.depth == self.max_delegation_depth:
            return type("DelegateKani", (*self.always_included_mixins, ReDelBase), {})
        else:
            return type("DelegateKani", (*self.always_included_mixins, ReDelBase, self.delegation_scheme), {})

    # noinspection PyPep8Naming
    async def create_delegate_kani(self):
        DelegateKani = await self.build_delegate_type()
        # then create an instance of that type
        name = self.namer.get_name()
        return DelegateKani(
            self.engine,
            # redel args
            delegation_scheme=self.delegation_scheme,
            always_included_mixins=self.always_included_mixins,
            # app args
            app=self.app,
            parent=self,
            system_prompt=DELEGATE_KANPAI,
            name=name,
        )


def build_root_type(delegation_scheme: type) -> Type[ReDelBase]:
    """Dynamically create the root type for the kani delegation tree."""
    # noinspection PyTypeChecker
    return type("RootKani", (ReDelBase, delegation_scheme), {})
