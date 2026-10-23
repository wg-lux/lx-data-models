"""Validated descriptive analysis; inferential estimators can consume these counts."""

import json
from collections.abc import Sequence
from hashlib import sha256
from typing import cast

from lx_dtypes.models.contracts.study_analysis import (
    StudyAnalysisDefinition,
    StudyAnalysisUnit,
    StudyDatasetStatistics,
    StudyEndpointStatistics,
    StudyFindingReference,
    StudyPredicate,
    StudyRole,
    StudyRule,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.validation import assess_examination

from .study_linkage import latest_study_choices


def _names(value: str | list[str]) -> list[str]:
    return [value] if isinstance(value, str) else value


def _rules(definition: StudyAnalysisDefinition) -> list[StudyRule]:
    result = [group.rule for group in definition.groups]
    if definition.inclusion is not None:
        result.append(definition.inclusion)
    for endpoint in definition.endpoints:
        result.extend([endpoint.positive, endpoint.negative])
        if endpoint.eligible is not None:
            result.append(endpoint.eligible)
    return result


def validate_study_analysis(
    definition: StudyAnalysisDefinition, knowledge_base: KnowledgeBase
) -> None:
    """Check the rule schema and every terminology reference, including drafts."""
    definition = StudyAnalysisDefinition.model_validate(definition.model_dump())
    identity = knowledge_base.config.knowledge_base_identity
    if (definition.module, definition.version) != (
        identity.knowledge_base_module,
        identity.knowledge_base_version,
    ):
        raise ValueError("analysis requires its exact knowledge-base identity")
    if definition.unit_finding not in knowledge_base.finding:
        raise ValueError("unknown analysis unit finding")
    for rule in _rules(definition):
        for predicate in rule.predicates:
            classification = knowledge_base.classification.get(predicate.classification)
            if classification is None:
                raise ValueError("unknown rule classification")
            choices = _names(classification.classification_choices)
            if predicate.descriptor is not None:
                if (
                    predicate.descriptor
                    not in knowledge_base.classification_choice_descriptor
                ):
                    raise ValueError("unknown rule descriptor")
                descriptor = knowledge_base.classification_choice_descriptor[
                    predicate.descriptor
                ]
                if (
                    predicate.operator in {"ge", "gt", "le", "lt"}
                    and not descriptor.is_numeric
                ):
                    raise ValueError(
                        "numeric rule comparisons require a numeric descriptor"
                    )
                if predicate.operator in {"eq", "ne"}:
                    if descriptor.is_boolean and not isinstance(predicate.value, bool):
                        raise ValueError(
                            "boolean rule descriptors require boolean operands"
                        )
                    if descriptor.is_numeric and (
                        isinstance(predicate.value, bool)
                        or not isinstance(predicate.value, float)
                    ):
                        raise ValueError(
                            "numeric rule descriptors require numeric operands"
                        )
                    if descriptor.is_text and not isinstance(predicate.value, str):
                        raise ValueError(
                            "text rule descriptors require string operands"
                        )
                if not any(
                    predicate.descriptor
                    in _names(
                        knowledge_base.classification_choice[
                            name
                        ].classification_choice_descriptors
                    )
                    for name in choices
                ):
                    raise ValueError(
                        "rule descriptor is not permitted by its classification"
                    )
            elif predicate.operator != "present":
                values = (
                    predicate.value
                    if isinstance(predicate.value, list)
                    else [predicate.value]
                )
                if any(value not in choices for value in values):
                    raise ValueError(
                        "rule choice is not permitted by its classification"
                    )
            if predicate.role == "index" and predicate.classification not in _names(
                knowledge_base.finding[definition.unit_finding].classifications
            ):
                raise ValueError(
                    "rule classification is not permitted by its unit finding"
                )


def _predicate(
    predicate: StudyPredicate, findings: dict[StudyRole, PFinding]
) -> bool | None:
    finding = findings.get(predicate.role)
    if finding is None or not finding.patient_finding_classifications:
        return None
    choices = [
        choice
        for choice in latest_study_choices(finding)
        if choice.classification == predicate.classification
    ]
    if len(choices) != 1:
        return None
    if predicate.descriptor is None:
        value: object = choices[0].classification_choice
    else:
        descriptors = [
            item
            for item in choices[0].patient_finding_classification_choice_descriptors
            if item.classification_choice_descriptor == predicate.descriptor
        ]
        if len(descriptors) != 1 or descriptors[0].descriptor_value is None:
            return None
        value = descriptors[0].descriptor_value
    if predicate.operator == "present":
        return value != ""
    operand = predicate.value
    if predicate.operator == "in":
        return value in cast(list[str], operand)
    if predicate.operator == "eq":
        return value == operand
    if predicate.operator == "ne":
        return value != operand
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    bound = cast(float, operand)
    if predicate.operator == "ge":
        return value >= bound
    if predicate.operator == "gt":
        return value > bound
    if predicate.operator == "le":
        return value <= bound
    return value < bound


def _rule(rule: StudyRule | None, findings: dict[StudyRole, PFinding]) -> bool | None:
    if rule is None:
        return True
    values = [_predicate(predicate, findings) for predicate in rule.predicates]
    if rule.mode == "all":
        return False if False in values else None if None in values else True
    return True if True in values else None if None in values else False


def _resolve(
    unit: StudyAnalysisUnit,
    records: dict[str, PExamination],
    definition: StudyAnalysisDefinition,
) -> dict[StudyRole, PFinding]:
    result: dict[StudyRole, PFinding] = {}
    index_record = records.get(unit.index.record_uuid)
    if index_record is None:
        raise ValueError("analysis unit references an unavailable record")
    role_records: dict[StudyRole, PExamination] = {}
    for role in ("index", "polyp", "previous_follow_up", "follow_up"):
        typed_role = cast(StudyRole, role)
        reference: StudyFindingReference | None = getattr(unit, role)
        if reference is None:
            continue
        record = records.get(reference.record_uuid)
        if record is None or record.patient != index_record.patient:
            raise ValueError(
                "analysis unit crosses patient or available dataset boundaries"
            )
        try:
            finding = record.get_finding_by_uuid(reference.finding_uuid)
        except KeyError as error:
            raise ValueError(
                "analysis unit references an unavailable finding"
            ) from error
        role_records[typed_role] = record
        result[typed_role] = finding
    if result["index"].finding != definition.unit_finding:
        raise ValueError("analysis unit has the wrong index finding")
    if "polyp" in role_records and role_records["polyp"].uuid != index_record.uuid:
        raise ValueError("index polyp must belong to the index examination")
    previous_record = index_record
    for role in ("previous_follow_up", "follow_up"):
        record = role_records.get(cast(StudyRole, role))
        if record is not None:
            if (
                record.date is None
                or previous_record.date is None
                or record.date <= previous_record.date
            ):
                raise ValueError(
                    "follow-up roles require strictly ordered examination dates"
                )
            previous_record = record
    return result


def evaluate_study_dataset(
    definition: StudyAnalysisDefinition,
    records: Sequence[PExamination],
    knowledge_base: KnowledgeBase,
    *,
    units: Sequence[StudyAnalysisUnit] | None = None,
) -> StudyDatasetStatistics:
    """Return explicit binary denominators; unknowns never become negative outcomes.

    Hosts supply authorized records and verified linkage units. Without units,
    each matching finding is one index unit and other roles remain unavailable.
    No significance test, causal contrast, or independence assumption is made.
    """
    definition = StudyAnalysisDefinition.model_validate(definition.model_dump())
    validate_study_analysis(definition, knowledge_base)
    if definition.status != "ready":
        raise ValueError("draft analysis requires protocol decisions before evaluation")
    record_map: dict[str, PExamination] = {}
    for source in records:
        record = PExamination.model_validate(source.model_dump())
        if (record.knowledge_base_module, record.knowledge_base_version) != (
            definition.module,
            definition.version,
        ):
            raise ValueError(
                "dataset records require the exact analysis terminology identity"
            )
        if not assess_examination(knowledge_base, record).ok:
            raise ValueError("dataset contains an invalid ledger record")
        if str(record.uuid) in record_map:
            raise ValueError("duplicate dataset examination")
        record_map[str(record.uuid)] = record
    if units is None:
        units = [
            StudyAnalysisUnit(
                index=StudyFindingReference(
                    record_uuid=str(record.uuid), finding_uuid=str(finding.uuid)
                )
            )
            for record in records
            for finding in record.patient_findings
            if finding.finding == definition.unit_finding
        ]
    seen: set[tuple[str, str]] = set()
    counts = {
        (group.name, endpoint.name): {
            "numerator": 0,
            "negative": 0,
            "missing": 0,
            "ineligible": 0,
            "eligibility_unknown": 0,
            "conflicting": 0,
        }
        for group in definition.groups
        for endpoint in definition.endpoints
    }
    included = excluded = unknown = unassigned = ambiguous = 0
    for source_unit in units:
        unit = StudyAnalysisUnit.model_validate(source_unit.model_dump())
        key = (unit.index.record_uuid, unit.index.finding_uuid)
        if key in seen:
            raise ValueError("duplicate index analysis unit")
        seen.add(key)
        findings = _resolve(unit, record_map, definition)
        eligible = _rule(definition.inclusion, findings)
        if eligible is False:
            excluded += 1
            continue
        if eligible is None:
            unknown += 1
            continue
        group_states = [
            (group.name, _rule(group.rule, findings)) for group in definition.groups
        ]
        matches = [name for name, state in group_states if state is True]
        if len(matches) > 1:
            ambiguous += 1
            continue
        if len(matches) != 1 or any(state is None for _, state in group_states):
            unassigned += 1
            continue
        included += 1
        for endpoint in definition.endpoints:
            bucket = counts[(matches[0], endpoint.name)]
            eligible = _rule(endpoint.eligible, findings)
            if eligible is False:
                bucket["ineligible"] += 1
                continue
            if eligible is None:
                bucket["eligibility_unknown"] += 1
                continue
            positive = _rule(endpoint.positive, findings)
            negative = _rule(endpoint.negative, findings)
            if positive is True and negative is True:
                bucket["conflicting"] += 1
            elif positive is True and negative is False:
                bucket["numerator"] += 1
            elif negative is True and positive is False:
                bucket["negative"] += 1
            else:
                bucket["missing"] += 1
    endpoints: list[StudyEndpointStatistics] = []
    for (group, endpoint), values in counts.items():
        denominator = values["numerator"] + values["negative"]
        endpoints.append(
            StudyEndpointStatistics(
                group=group,
                endpoint=endpoint,
                denominator=denominator,
                rate=values["numerator"] / denominator if denominator else None,
                **values,
            )
        )
    digest = sha256(
        json.dumps(
            definition.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    return StudyDatasetStatistics(
        analysis_name=definition.name,
        analysis_digest=f"sha256:{digest}",
        module=definition.module,
        version=definition.version,
        total_records=len(record_map),
        total_units=len(units),
        included_units=included,
        excluded_units=excluded,
        inclusion_unknown=unknown,
        unassigned_units=unassigned,
        ambiguous_units=ambiguous,
        endpoints=endpoints,
    )
