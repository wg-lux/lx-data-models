from heapq import heappop, heappush
from pathlib import Path
from typing import TYPE_CHECKING

from lx_dtypes.models.interface.data_roots import default_data_roots

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBaseConfig import (
        KnowledgeBaseConfig,
    )


def _default_dataloader_dirs_factory() -> list[Path]:
    return list(default_data_roots())


def resolve_kb_module_load_order(
    modules: dict[str, "KnowledgeBaseConfig"],
    preferred_order: list[str],
) -> list[str]:
    """Topologically sort modules while respecting preferred ordering when possible."""

    if not modules:
        return []

    adjacency: dict[str, set[str]] = {name: set() for name in modules}
    indegree: dict[str, int] = {name: 0 for name in modules}

    for module_name, module_config in modules.items():
        for dependency in module_config.depends_on:
            if dependency not in modules:
                raise ValueError(
                    f"Module '{module_name}' depends on '{dependency}', which was not collected for ordering.",
                )
            adjacency[dependency].add(module_name)
            indegree[module_name] += 1

    preferred_index = {name: idx for idx, name in enumerate(preferred_order)}

    def priority(name: str) -> tuple[int, str]:
        return (preferred_index.get(name, len(preferred_index)), name)

    heap: list[tuple[int, str]] = []
    for name, degree in indegree.items():
        if degree == 0:
            heappush(heap, priority(name))

    load_order: list[str] = []
    while heap:
        _, node = heappop(heap)
        load_order.append(node)
        for dependent in sorted(adjacency[node]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heappush(heap, priority(dependent))

    if len(load_order) != len(modules):
        unresolved = ", ".join(sorted(set(modules.keys()) - set(load_order)))
        raise ValueError(f"Circular dependency detected among modules: {unresolved}")

    return load_order
