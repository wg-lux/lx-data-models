"""Resolve and evaluate YAML-authored numeric classification rules."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import yaml

from lx_dtypes.models.contracts.numeric_classification import (
    NumericClassificationResult,
    NumericClassificationRules,
    NumericMeasurement,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base


def read_rules(path: Path) -> NumericClassificationRules:
    """Parse a strict sidecar, including duplicate-key rejection."""
    raw = path.read_text(encoding="utf-8")
    node = yaml.compose(raw, Loader=yaml.SafeLoader)

    def check(node: yaml.Node) -> None:
        if isinstance(node, yaml.MappingNode):
            keys: set[str] = set()
            for key, value in node.value:
                if (
                    not isinstance(key, yaml.ScalarNode)
                    or key.tag != "tag:yaml.org,2002:str"
                ):
                    raise ValueError("rule mapping keys must be strings")
                if key.value in keys:
                    raise ValueError(f"duplicate rule mapping key: {key.value}")
                keys.add(key.value)
                check(value)
        elif isinstance(node, yaml.SequenceNode):
            for child in node.value:
                check(child)

    if node is not None:
        check(node)
    return NumericClassificationRules.model_validate(yaml.safe_load(raw))


def load_numeric_classification(
    module: str, *, version: str
) -> NumericClassificationRules:
    """Resolve the exact artifact first; never infer a version from a path."""
    kb: KnowledgeBase = load_knowledge_base(module, version=version)
    kb.export_core_concepts()
    if kb.config.source_file is None:
        raise ValueError("resolved knowledge base has no source config")
    rules = read_rules(kb.config.source_file.parent / "numeric_rules.yml")
    if rules.knowledge_base != kb.config.knowledge_base_identity:
        raise ValueError("numeric rules identity differs from resolved knowledge base")
    classification = kb.get_classification(name=rules.classification)
    if set(classification.classification_choices) != {r.choice for r in rules.rules}:
        raise ValueError("numeric rules must cover exactly the classification choices")
    if rules.unit not in kb.unit:
        raise ValueError("numeric rules reference an unknown unit")
    return rules


def validate_measurement_source(
    measurement: NumericMeasurement, kb: KnowledgeBase
) -> None:
    """Verify that the source descriptor and unit belong to the stated KB."""
    if measurement.source_knowledge_base != kb.config.knowledge_base_identity:
        raise ValueError(
            "measurement source identity differs from source knowledge base"
        )
    descriptor = kb.get_classification_choice_descriptor(name=measurement.descriptor)
    if not descriptor.is_numeric or descriptor.unit != measurement.unit:
        raise ValueError(
            "measurement must reference a numeric descriptor with the same unit"
        )
    if not descriptor.numeric_min <= measurement.value <= descriptor.numeric_max:
        raise ValueError("measurement is outside its source descriptor bounds")


def classify_measurement(
    measurement: NumericMeasurement,
    rules: NumericClassificationRules,
) -> NumericClassificationResult:
    """Apply a validated rule set; no rounding, conversion or source mutation."""
    if (
        measurement.unit != rules.unit
        or measurement.descriptor != rules.input_descriptor
    ):
        raise ValueError("measurement unit or descriptor differs from numeric rules")
    if rules.resolution == "whole_number" and not measurement.value.is_integer():
        raise ValueError(
            "this rule set requires a whole-number measurement; no rounding is applied"
        )
    matches = [rule for rule in rules.rules if rule.contains(measurement.value)]
    if len(matches) != 1:
        raise ValueError("measurement is outside the classification domain")
    return NumericClassificationResult(
        measurement=measurement,
        knowledge_base=rules.knowledge_base,
        classification=rules.classification,
        choice=matches[0].choice,
        rules_sha256=sha256(rules.model_dump_json().encode("utf-8")).hexdigest(),
    )


__all__ = [
    "classify_measurement",
    "load_numeric_classification",
    "validate_measurement_source",
]
