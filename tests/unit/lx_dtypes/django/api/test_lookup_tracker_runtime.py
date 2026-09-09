from __future__ import annotations

from lx_dtypes.django.api.lookup_tracker import (
    consume_runtime_lookup_trackers,
    register_runtime_lookup_tracker,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


def test_runtime_lookup_tracker_registers_deduplicates_and_clears(
    knowledge_base_fixture: KnowledgeBase,
) -> None:
    kb = knowledge_base_fixture.model_copy(deep=True)

    assert consume_runtime_lookup_trackers() == []

    register_runtime_lookup_tracker(kb)
    register_runtime_lookup_tracker(kb)

    consumed = consume_runtime_lookup_trackers()
    assert consumed == [kb]
    assert consume_runtime_lookup_trackers() == []
