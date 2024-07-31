"""
This module contains utilities for indexing a directory that might contain ReDel saves.
"""

import json
from pathlib import Path
from typing import Iterable

from .models import SaveMeta


def find_saves(fp: Path) -> Iterable[SaveMeta]:
    """Recursively yield saves starting from a given root dir."""
    state_fp = fp / "state.json"
    event_fp = fp / "events.jsonl"
    if state_fp.exists():
        with open(state_fp, encoding="utf-8") as f:
            data = json.load(f)
            yield SaveMeta(
                grouping_prefix=fp.parent.parts,
                state_fp=state_fp,
                event_fp=event_fp,
                id=data["id"],
                title=data["title"],
                last_modified=data["last_modified"],
                n_events=data["n_events"],
            )

    # recurse
    for subdir in fp.iterdir():
        if not subdir.is_dir():
            continue
        yield from find_saves(subdir)
