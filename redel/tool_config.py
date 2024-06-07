import itertools
import logging
from typing import Iterable, TypedDict

log = logging.getLogger(__name__)


class ToolConfig(TypedDict, total=False):
    always_include: bool
    """If true, each delegate kani will *always* inherit from this class. Defaults to False."""
    kwargs: dict
    """Keyword arguments to pass to the constructor of this class. Defaults to ``{}``."""


ToolConfigType = dict[type, ToolConfig]


def validate_tool_configs(configs: ToolConfigType):
    """Check for common errors and raise ValueError if present.

    Currently checked:
    - overlapping kwargs
    """
    # TODO: echo the config
    # if echo:
    #     log.info()

    # check for overlapping kwargs
    all_kwarg_keys = list(itertools.chain.from_iterable(cfg.get("kwargs", {}).keys() for cfg in configs.values()))
    duplicate_kwarg_keys = [k for k in all_kwarg_keys if all_kwarg_keys.count(k) > 1]
    if duplicate_kwarg_keys:
        raise ValueError(f"Found duplicate kwargs in tool configurations! Duplicated kwargs: {duplicate_kwarg_keys}")


def get_always_included_types(configs: ToolConfigType) -> tuple[type, ...]:
    """Return a tuple of all types in the config that are always included."""
    return tuple(t for t, config in configs.items() if config.get("always_include", False))


def get_tool_cls_kwargs(configs: ToolConfigType, bases: Iterable[type]) -> dict:
    """Return kwargs for the given bases and the given config.

    If a passed class is not in the config, ignores it. (This lets you call this with ``bases=t.__bases__``.)
    """
    kwargs = {}
    for t in bases:
        # get the type's config kwargs
        if t not in configs:
            continue
        cfg_kwargs = configs[t].get("kwargs")
        if not cfg_kwargs:
            continue
        # add them to kwargs
        kwargs.update(cfg_kwargs)
    return kwargs
