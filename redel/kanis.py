import datetime
import logging
from typing import Iterable

from kani import ChatMessage
from kani.engines import BaseEngine

from .base_kani import BaseKani
from .namer import Namer

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
    """Base class for recursive delegation kanis."""

    def __init__(
        self,
        *args,
        # prompting
        delegate_engine: BaseEngine = None,
        delegate_system_prompt: str | None = DELEGATE_KANPAI,
        # delegation
        delegation_scheme: type,
        always_included_mixins: Iterable[type] = (),
        max_delegation_depth: int = None,
        # base kani stuff
        delegate_kani_kwargs: dict = None,
        **kwargs,
    ):
        """
        :param delegate_system_prompt: The system prompt to use for each delegate kani.
        :param delegation_scheme: The delegation scheme to use (Delegate1Mixin or DelegateWaitMixin).
        :param max_delegation_depth: The maximum depth of the delegation chain - any kanis created at this depth will
            not inherit from the *delegation_scheme*.
        :param always_included_mixins: Mixins to include for each delegate (but not the root).
        :param delegate_kani_kwargs: Additional kwargs to pass to each constructed delegate kani.
        """
        kwargs.setdefault("retry_attempts", 10)
        super().__init__(*args, **kwargs)

        if delegate_engine is None:
            delegate_engine = self.engine
        if delegate_kani_kwargs is None:
            delegate_kani_kwargs = {}

        self.namer = Namer()
        self.delegate_engine = delegate_engine
        self.delegate_system_prompt = delegate_system_prompt
        self.delegation_scheme = delegation_scheme
        self.max_delegation_depth = max_delegation_depth
        self.always_included_mixins = always_included_mixins
        self.delegate_kani_kwargs = delegate_kani_kwargs

    async def get_prompt(self) -> list[ChatMessage]:
        if self.system_prompt is not None:
            self.always_included_messages[0] = ChatMessage.system(get_system_prompt(self))
        return await super().get_prompt()

    # noinspection PyPep8Naming
    async def create_delegate_kani(self):
        # construct the type for the new delegate, TODO with the retrieved functions to use
        if self.depth == self.max_delegation_depth:
            DelegateKani = type("DelegateKani", (*self.always_included_mixins, ReDelBase), {})
        else:
            DelegateKani = type("DelegateKani", (*self.always_included_mixins, ReDelBase, self.delegation_scheme), {})

        # then create an instance of that type
        name = self.namer.get_name()
        return DelegateKani(
            self.delegate_engine,
            # redel args
            delegation_scheme=self.delegation_scheme,
            always_included_mixins=self.always_included_mixins,
            # app args
            app=self.app,
            parent=self,
            name=name,
            # kani args
            system_prompt=self.delegate_system_prompt,
            **self.delegate_kani_kwargs,
        )


def create_root_kani(
    *args, delegation_scheme: type | None, always_included_mixins: Iterable[type], root_has_functions: bool, **kwargs
) -> ReDelBase:
    """Create the root kani for the kani delegation tree."""
    bases = (ReDelBase, delegation_scheme) if delegation_scheme is not None else (ReDelBase,)
    if root_has_functions:
        t = type("RootKani", (*always_included_mixins, *bases), {})
    else:
        t = type("RootKani", bases, {})
    return t(*args, delegation_scheme=delegation_scheme, always_included_mixins=always_included_mixins, **kwargs)
