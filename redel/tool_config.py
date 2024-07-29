import logging
from typing import TypeVar, TypedDict

from redel.tools import ToolBase

log = logging.getLogger(__name__)

_ToolBaseT = TypeVar("_ToolBaseT", bound=ToolBase)


class ToolConfig(TypedDict, total=False):
    """A tool's config should be a dictionary with any of the following keys:"""

    always_include: bool
    """If true, each delegate kani will *always* have access to this tool. Defaults to False."""
    always_include_root: bool
    """If true, the *root* kani will have access to this tool (but not necessarily delegates unless ``always_include`` 
    is also set)."""
    kwargs: dict
    """Keyword arguments to pass to the constructor of this class. Defaults to ``{}``.
    
    The tool class' constructor will be called each time a new instance is bound to a new kani. Each kani will have
    its own instance of the tool.
    """


ToolConfigType = dict[type[_ToolBaseT], ToolConfig]


def validate_tool_configs(configs: ToolConfigType):
    """Check for common errors and raise ValueError if present.

    Currently checked:
    - if there is potential for duplicate function names
    """
    # TODO: echo the config
    # if echo:
    #     log.info()

    # check for overlapping kwargs
    # all_kwarg_keys = list(itertools.chain.from_iterable(cfg.get("kwargs", {}).keys() for cfg in configs.values()))
    # duplicate_kwarg_keys = [k for k in all_kwarg_keys if all_kwarg_keys.count(k) > 1]
    # if duplicate_kwarg_keys:
    #     raise ValueError(f"Found duplicate kwargs in tool configurations! Duplicated kwargs: {duplicate_kwarg_keys}")
