"""Reproducible synthetic graph timings; no clinical records or network I/O.

Run from the repository root: python scripts/benchmark_graph_resolution.py
Timings are measurements, not a clinical deployment latency guarantee.
"""

from __future__ import annotations

import argparse
import json
from statistics import median
from time import perf_counter
from collections.abc import Callable

from lx_dtypes.models.contracts.fhir_clinical import FhirClinicalBundle
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.knowledge_base_graph import (
    KnowledgeBaseGraphResolver,
    build_examination_reporting_context,
    build_knowledge_base_graph_snapshot,
)


class SyntheticKnowledgeBase:
    def __init__(self, count: int) -> None:
        self.count = count
        self.report_template: dict[str, object] = {}

    def export_core_concepts(self) -> JsonObject:
        return {
            "module_name": "synthetic",
            "knowledge_base_module": "synthetic",
            "knowledge_base_version": "1.0.0",
            "finding": [{"name": f"finding_{i}"} for i in range(self.count)],
            "examination": [
                {
                    "name": "exam",
                    "findings": [f"finding_{i}" for i in range(self.count)],
                },
                {
                    "name": "small_exam",
                    "findings": [f"finding_{i}" for i in range(min(self.count, 10))],
                },
            ],
        }

    def export_report_template(self, name: str) -> JsonObject:
        raise KeyError(name)

    def get_report_template_lifecycle_status(self, name: str) -> str:
        raise KeyError(name)


def clinical_bundle(count: int) -> FhirClinicalBundle:
    code = {"coding": [{"system": "urn:synthetic", "code": "result"}]}
    return FhirClinicalBundle.model_validate(
        {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "synthetic"}},
                *(
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": f"o-{i}",
                            "status": "final",
                            "code": code,
                            "subject": {"reference": "Patient/synthetic"},
                            "valueInteger": i,
                        }
                    }
                    for i in range(count)
                ),
                {
                    "resource": {
                        "resourceType": "DiagnosticReport",
                        "id": "report",
                        "status": "final",
                        "code": code,
                        "subject": {"reference": "Patient/synthetic"},
                        "result": [
                            {"reference": f"Observation/o-{i}"} for i in range(count)
                        ],
                    }
                },
            ],
        }
    )


def elapsed_ms(operation: Callable[[], object], repeats: int) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        start = perf_counter()
        operation()
        samples.append((perf_counter() - start) * 1000)
    return round(median(samples), 3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 1000, 5000])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1 or any(size < 1 or size > 100000 for size in args.sizes):
        parser.error("positive repeats and graph sizes from 1 to 100000 are required")
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="synthetic", knowledge_base_version="1.0.0"
    )
    for count in args.sizes:
        kb = SyntheticKnowledgeBase(count)
        snapshot = build_knowledge_base_graph_snapshot(kb, identity=identity)
        resolver = KnowledgeBaseGraphResolver(snapshot)
        bundle = clinical_bundle(count)
        print(
            json.dumps(
                {
                    "nodes_or_observations": count,
                    "repeats": args.repeats,
                    "statistic": "median_ms",
                    "fhir_resolved_reports": elapsed_ms(
                        bundle.resolved_reports, args.repeats
                    ),
                    "graph_snapshot": elapsed_ms(
                        lambda: build_knowledge_base_graph_snapshot(
                            kb, identity=identity
                        ),
                        args.repeats,
                    ),
                    "reporting_context": elapsed_ms(
                        lambda: build_examination_reporting_context(
                            snapshot, examination_name="exam"
                        ),
                        args.repeats,
                    ),
                    "indexed_small_context": elapsed_ms(
                        lambda: resolver.reporting_context("small_exam"), args.repeats
                    ),
                }
            )
        )


if __name__ == "__main__":
    main()
