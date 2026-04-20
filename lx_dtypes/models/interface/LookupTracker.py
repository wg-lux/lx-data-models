from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LookupEdge:
    source: str
    target: str


@dataclass(frozen=True)
class LookupKeyEdge:
    source: str
    target: str
    key: str
    found: bool


class KnowledgeBaseLookupTracker:
    """
    Track knowledge-base lookup activity and export graph-oriented summaries.
    """

    def __init__(self) -> None:
        self._edge_counts: Counter[LookupEdge] = Counter()
        self._key_counts: Counter[LookupKeyEdge] = Counter()

    def record_lookup(
        self,
        *,
        source: str,
        target: str,
        key: str,
        found: bool,
    ) -> None:
        normalized_source = source.strip() or "knowledge_base"
        normalized_target = target.strip() or "unknown"
        normalized_key = str(key).strip()

        self._edge_counts[LookupEdge(normalized_source, normalized_target)] += 1
        self._key_counts[
            LookupKeyEdge(
                normalized_source,
                normalized_target,
                normalized_key,
                found,
            )
        ] += 1

    def reset(self) -> None:
        self._edge_counts.clear()
        self._key_counts.clear()

    @property
    def total_lookup_count(self) -> int:
        return sum(self._edge_counts.values())

    def as_summary(self) -> dict[str, Any]:
        edge_counts = [
            {
                "source": edge.source,
                "target": edge.target,
                "lookup_count": count,
            }
            for edge, count in self._edge_counts.most_common()
        ]
        key_counts = [
            {
                "source": key_edge.source,
                "target": key_edge.target,
                "key": key_edge.key,
                "found": key_edge.found,
                "lookup_count": count,
            }
            for key_edge, count in self._key_counts.most_common()
        ]
        return {
            "total_lookup_count": self.total_lookup_count,
            "edge_counts": edge_counts,
            "key_counts": key_counts,
        }

    def export_mermaid_graph(self) -> str:
        lines: list[str] = ["graph LR"]
        if not self._edge_counts:
            lines.append('  kb["knowledge_base"]')
            return "\n".join(lines)

        lines.append('  kb["knowledge_base"]')
        added_nodes: set[str] = {"kb"}
        sorted_edges = sorted(
            self._edge_counts.items(),
            key=lambda item: (-item[1], item[0].source, item[0].target),
        )
        for edge, count in sorted_edges:
            source_node = _slugify_node(edge.source)
            target_node = _slugify_node(edge.target)
            if source_node not in added_nodes:
                lines.append(f'  {source_node}["{edge.source}"]')
                added_nodes.add(source_node)
            if target_node not in added_nodes:
                lines.append(f'  {target_node}["{edge.target}"]')
                added_nodes.add(target_node)
            lines.append(f"  {source_node} -->|{count}| {target_node}")
        return "\n".join(lines)

    def export_dot_graph(self) -> str:
        lines: list[str] = ["digraph knowledge_base_lookup_graph {"]
        lines.append('  rankdir="LR";')
        lines.append('  "knowledge_base";')

        if self._edge_counts:
            sorted_edges = sorted(
                self._edge_counts.items(),
                key=lambda item: (-item[1], item[0].source, item[0].target),
            )
            for edge, count in sorted_edges:
                lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{count}"];')
        lines.append("}")
        return "\n".join(lines)

    def compare_to_snomed(
        self,
        *,
        snomed_lookup_count: int,
        lx_elapsed_seconds: float | None = None,
        snomed_elapsed_seconds: float | None = None,
    ) -> dict[str, Any]:
        lx_lookup_count = self.total_lookup_count
        comparison: dict[str, Any] = {
            "lx_lookup_count": lx_lookup_count,
            "snomed_lookup_count": max(snomed_lookup_count, 0),
            "lookup_count_delta": lx_lookup_count - max(snomed_lookup_count, 0),
            "lookup_count_ratio_lx_over_snomed": (
                float(lx_lookup_count) / float(snomed_lookup_count)
                if snomed_lookup_count > 0
                else None
            ),
        }

        if lx_elapsed_seconds is not None:
            comparison["lx_elapsed_seconds"] = lx_elapsed_seconds
        if snomed_elapsed_seconds is not None:
            comparison["snomed_elapsed_seconds"] = snomed_elapsed_seconds
        if (
            lx_elapsed_seconds is not None
            and snomed_elapsed_seconds is not None
            and snomed_elapsed_seconds > 0
        ):
            comparison["elapsed_time_ratio_lx_over_snomed"] = (
                lx_elapsed_seconds / snomed_elapsed_seconds
            )
        return comparison


def _slugify_node(value: str) -> str:
    lowered = value.lower()
    out_chars: list[str] = []
    for char in lowered:
        if char.isalnum():
            out_chars.append(char)
        else:
            out_chars.append("_")
    out = "".join(out_chars).strip("_")
    return out or "node"
