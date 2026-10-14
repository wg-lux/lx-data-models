#!/usr/bin/env python3
"""Import complete clinical report graphs from a public FHIR R4 server."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

from lx_dtypes.models.contracts.fhir_clinical import FhirClinicalBundle

DEFAULT_ENDPOINT = "https://hapi.fhir.org/baseR4"
DEFAULT_OUTPUT = Path("temp/generated_exports/hapi_clinical_import.yaml")
SUPPORTED_VALUE_FIELDS = (
    "valueQuantity",
    "valueString",
    "valueBoolean",
    "valueInteger",
    "valueDecimal",
    "valueCodeableConcept",
)
REFERENCE_RE = re.compile(r"(Patient|Observation)/([^/?#]+)")
LANGUAGE_TAG_RE = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
OBSERVATION_FIELDS = (
    "resourceType",
    "id",
    "status",
    "category",
    "code",
    "subject",
    "effectiveDateTime",
    "issued",
    *SUPPORTED_VALUE_FIELDS,
    "component",
    "interpretation",
    "referenceRange",
    "bodySite",
    "method",
)
REPORT_FIELDS = (
    "resourceType",
    "id",
    "status",
    "category",
    "code",
    "subject",
    "effectiveDateTime",
    "issued",
    "result",
)


def _normalise_reference(reference: str) -> str:
    match = REFERENCE_RE.search(reference)
    if match is None:
        return reference
    return f"{match.group(1)}/{match.group(2)}"


def _has_coded_concept(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    coding = value.get("coding")
    return isinstance(coding, list) and any(
        isinstance(item, Mapping) and item.get("system") and item.get("code")
        for item in coding
    )


def _component_is_supported(component: object) -> bool:
    if not isinstance(component, Mapping) or not _has_coded_concept(
        component.get("code")
    ):
        return False
    return (
        sum(component.get(field) is not None for field in SUPPORTED_VALUE_FIELDS) == 1
    )


def _observation_is_supported(resource: Mapping[str, Any]) -> bool:
    subject = resource.get("subject")
    if not isinstance(subject, Mapping):
        return False
    subject_reference = _normalise_reference(str(subject.get("reference", "")))
    top_level_values = sum(
        resource.get(field) is not None for field in SUPPORTED_VALUE_FIELDS
    )
    components = resource.get("component")
    has_supported_components = (
        isinstance(components, list)
        and bool(components)
        and all(_component_is_supported(component) for component in components)
    )
    return (
        resource.get("resourceType") == "Observation"
        and bool(resource.get("id"))
        and bool(resource.get("status"))
        and _has_coded_concept(resource.get("code"))
        and subject_reference.startswith("Patient/")
        and (
            top_level_values == 1
            or (top_level_values == 0 and has_supported_components)
        )
    )


def _resource_index(bundle: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for entry in bundle.get("entry", []):
        if not isinstance(entry, Mapping):
            continue
        resource = entry.get("resource")
        if not isinstance(resource, dict):
            continue
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if resource_type and resource_id:
            index[f"{resource_type}/{resource_id}"] = resource
    return index


def _select_fields(
    resource: Mapping[str, Any],
    fields: tuple[str, ...],
) -> dict[str, Any]:
    return {field: resource[field] for field in fields if field in resource}


def _clinical_subset(
    source_bundle: Mapping[str, Any],
    *,
    endpoint: str,
    language: str,
) -> dict[str, Any]:
    index = _resource_index(source_bundle)
    reports: list[dict[str, Any]] = []
    observations: dict[str, dict[str, Any]] = {}
    patient_ids: set[str] = set()

    for resource in index.values():
        if resource.get("resourceType") != "DiagnosticReport":
            continue
        subject = resource.get("subject")
        if not isinstance(subject, Mapping):
            continue
        patient_reference = _normalise_reference(str(subject.get("reference", "")))
        patient = index.get(patient_reference)
        if not patient or patient.get("resourceType") != "Patient":
            continue
        if not _has_coded_concept(resource.get("code")):
            continue

        result_items = resource.get("result")
        if not isinstance(result_items, list) or not result_items:
            continue
        result_references = [
            _normalise_reference(str(item.get("reference", "")))
            for item in result_items
            if isinstance(item, Mapping)
        ]
        linked_observations = [index.get(reference) for reference in result_references]
        if len(linked_observations) != len(result_items) or not all(
            observation is not None
            and _observation_is_supported(observation)
            and _normalise_reference(
                str(observation.get("subject", {}).get("reference", ""))
            )
            == patient_reference
            for observation in linked_observations
        ):
            continue

        report = _select_fields(resource, REPORT_FIELDS)
        report["subject"] = {"reference": patient_reference}
        report["result"] = [{"reference": reference} for reference in result_references]
        reports.append(report)
        patient_ids.add(patient_reference.removeprefix("Patient/"))

        for reference, observation in zip(
            result_references, linked_observations, strict=True
        ):
            assert observation is not None
            cleaned_observation = _select_fields(observation, OBSERVATION_FIELDS)
            cleaned_observation["subject"] = {"reference": patient_reference}
            observations[reference] = cleaned_observation

    if not reports:
        raise ValueError(
            "The FHIR response contained no complete supported report graphs"
        )

    entries: list[dict[str, Any]] = [
        {
            "fullUrl": f"{endpoint.rstrip('/')}/Patient/{patient_id}",
            # Public test servers may contain arbitrary user-entered demographics.
            # Only the stable reference target is needed for structural evaluation.
            "resource": {"resourceType": "Patient", "id": patient_id},
        }
        for patient_id in sorted(patient_ids)
    ]
    entries.extend(
        {
            "fullUrl": f"{endpoint.rstrip('/')}/{reference}",
            "resource": resource,
        }
        for reference, resource in sorted(observations.items())
    )
    entries.extend(
        {
            "fullUrl": f"{endpoint.rstrip('/')}/DiagnosticReport/{report['id']}",
            "resource": report,
        }
        for report in reports
    )

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "language": language,
        "timestamp": datetime.now(UTC).isoformat(),
        "meta": {
            "source": endpoint.rstrip("/"),
            "tag": [
                {
                    "system": "https://github.com/wg-lux/lx-data-models",
                    "code": "sanitized-public-test-data",
                    "display": (
                        "Patient demographics and free-text narratives removed; "
                        "FHIR resource IDs retained"
                    ),
                }
            ],
        },
        "entry": entries,
    }


def import_clinical_yaml(
    endpoint: str,
    output: Path,
    *,
    language: str,
    count: int,
) -> FhirClinicalBundle:
    if LANGUAGE_TAG_RE.fullmatch(language) is None:
        raise ValueError(
            "language must be an IETF language tag such as 'en', 'de', or 'de-DE'"
        )
    if count < 1:
        raise ValueError("count must be at least 1")

    query = urlencode(
        [
            ("_count", str(count)),
            ("_sort", "-_lastUpdated"),
            ("_include", "DiagnosticReport:result"),
            ("_include", "DiagnosticReport:subject"),
            ("_format", "json"),
        ],
    )
    request = Request(
        f"{endpoint.rstrip('/')}/DiagnosticReport?{query}",
        headers={
            "Accept": "application/fhir+json",
            "Accept-Language": language,
        },
    )
    with urlopen(request, timeout=60) as response:
        source_bundle = cast(dict[str, Any], json.loads(response.read()))
    if source_bundle.get("resourceType") != "Bundle":
        raise ValueError("FHIR server did not return a Bundle")

    document = _clinical_subset(
        source_bundle,
        endpoint=endpoint,
        language=language,
    )
    validated = FhirClinicalBundle.model_validate(document)
    validated.validate_clinical_links()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return validated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--language", default="de")
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()

    bundle = import_clinical_yaml(
        args.endpoint,
        args.output,
        language=args.language,
        count=args.count,
    )
    reports = bundle.resolved_reports()
    observations = {item.id for report in reports for item in report.observations}
    patients = {report.patient.id for report in reports}
    print(
        f"Wrote {args.output}: {len(reports)} DiagnosticReports, "
        f"{len(observations)} Observations, {len(patients)} sanitized Patients "
        f"(language={args.language!r})"
    )


if __name__ == "__main__":
    main()
