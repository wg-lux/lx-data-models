from heapq import heappop, heappush
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.knowledge_base_config import (
        KnowledgeBaseConfig,
    )


def resolve_kb_module_load_order(
    modules: Dict[str, "KnowledgeBaseConfig"],
    preferred_order: List[str],
) -> List[str]:
    """Topologically sort modules while respecting preferred ordering when possible."""

    if not modules:
        return []

    adjacency: Dict[str, Set[str]] = {name: set() for name in modules}
    indegree: Dict[str, int] = {name: 0 for name in modules}

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

    heap: List[Tuple[int, str]] = []
    for name, degree in indegree.items():
        if degree == 0:
            heappush(heap, priority(name))

    load_order: List[str] = []
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
