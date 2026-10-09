"""Reproduce the manuscript size comparison through the versioned resolver.

Run with --help for the explicit input and output paths. Registry provisioning
is a separate step documented in the knowledge-base authoring guide.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.numeric_classification import (
    NumericClassificationResult,
    NumericMeasurement,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base
from lx_dtypes.numeric_classification import (
    classify_measurement,
    load_numeric_classification,
    validate_measurement_source,
)


class _Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    observation_id: str = Field(min_length=1)
    value: float = Field(allow_inf_nan=False)


class ComparisonFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_knowledge_base: KnowledgeBaseIdentity
    descriptor: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    observations: list[_Observation] = Field(min_length=1)
    expected_choices: dict[str, list[str]]


def run_comparison(fixture_path: Path) -> list[NumericClassificationResult]:
    fixture = ComparisonFixture.model_validate(
        yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    )
    if len({item.observation_id for item in fixture.observations}) != len(
        fixture.observations
    ):
        raise ValueError("observation IDs must be unique")
    if set(fixture.expected_choices) != {"1.0.0", "2.0.0"}:
        raise ValueError("comparison requires expected results for both versions")
    source = fixture.source_knowledge_base
    source_kb: KnowledgeBase = load_knowledge_base(
        source.knowledge_base_module,
        version=source.knowledge_base_version,
    )
    source_kb.export_core_concepts()
    measurements = [
        NumericMeasurement(
            observation_id=item.observation_id,
            value=item.value,
            source_knowledge_base=source,
            descriptor=fixture.descriptor,
            unit=fixture.unit,
        )
        for item in fixture.observations
    ]
    for measurement in measurements:
        validate_measurement_source(measurement, source_kb)
    results: list[NumericClassificationResult] = []
    for version in ("1.0.0", "2.0.0"):
        rules = load_numeric_classification("polyp_size_category", version=version)
        version_results = [classify_measurement(value, rules) for value in measurements]
        if [result.choice for result in version_results] != fixture.expected_choices[
            version
        ]:
            raise ValueError(f"computed results differ from fixture for {version}")
        results.extend(version_results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("temp/generated_exports/classification_versioning"),
    )
    args = parser.parse_args()
    results = run_comparison(args.measurements)
    output: Path = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.yml").write_text(
        yaml.safe_dump([r.model_dump(mode="json") for r in results], sort_keys=False),
        encoding="utf-8",
    )
    with (output / "table4.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["observation_id", "size_mm", "1.0.0", "2.0.0"])
        labels: dict[tuple[str, str], str] = {}
        for version in ("1.0.0", "2.0.0"):
            kb: KnowledgeBase = load_knowledge_base(
                "polyp_size_category", version=version
            )
            for result in results:
                if result.knowledge_base.knowledge_base_version != version:
                    continue
                label = kb.get_classification_choice(name=result.choice).name_en
                if not label:
                    raise ValueError(
                        f"missing English label for {result.choice}@{version}"
                    )
                labels[(version, result.choice)] = label
        half = len(results) // 2
        for legacy, revised in zip(results[:half], results[half:], strict=True):
            writer.writerow(
                [
                    legacy.measurement.observation_id,
                    legacy.measurement.value,
                    labels[("1.0.0", legacy.choice)],
                    labels[("2.0.0", revised.choice)],
                ]
            )
    print(
        f"Verified {len(results)} interpretations; wrote {output / 'table4.csv'} and results.yml"
    )


if __name__ == "__main__":
    main()
