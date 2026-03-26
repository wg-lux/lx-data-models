"""Lightweight helpers that expose per-request KnowledgeBase lookup activity."""

from __future__ import annotations

import contextvars
from typing import List

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

_lookup_trackers: contextvars.ContextVar[List[KnowledgeBase] | None] = (
    contextvars.ContextVar("lx_lookup_trackers", default=None)
)


def register_runtime_lookup_tracker(kb: KnowledgeBase) -> None:
    """
    Record a KnowledgeBase so middleware or request-scoped services can emit its tracker.

    This function is idempotent for the same KnowledgeBase instance within the same
    execution context.
    """
    trackers = _lookup_trackers.get()
    if trackers is None:
        trackers = []
        _lookup_trackers.set(trackers)
    if kb not in trackers:
        trackers.append(kb)


def consume_runtime_lookup_trackers() -> List[KnowledgeBase]:
    """
    Return the list of registered KnowledgeBase instances and clear the slot.
    """
    trackers = _lookup_trackers.get()
    _lookup_trackers.set(None)
    return list(trackers or [])
