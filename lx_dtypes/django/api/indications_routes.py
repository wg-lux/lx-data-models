from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable, Dict, List, NoReturn, Optional, Protocol, Set, cast

from lx_dtypes.models.contracts.terminology_catalog import (
    IndicationCatalogDTO,
    LocalizedCatalogItem,
)

from . import findings_routes
from .request_types import BaseRequest


class _RouteDecorator(Protocol):
    def __call__(self, func: Callable[..., Any], /) -> Callable[..., Any]: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...


def _relation_items(relation: Any | None) -> list[Any]:
    all_ = getattr(relation, "all", None)
    if not callable(all_):
        return []
    items = all_()
    if not isinstance(items, Iterable):
        return []
    return list(cast(Iterable[Any], items))


def _serialize_relation_items(relation: Any | None) -> list[dict[str, Any]]:
    return [
        {
            "id": item.id,
            "name": item.name,
            "name_de": getattr(item, "name_de", ""),
            "name_en": getattr(item, "name_en", ""),
            "description": getattr(item, "description", None),
        }
        for item in _relation_items(relation)
    ]


def _serialize_indication(indication: Any) -> Dict[str, Any]:
    indication_types_relation = getattr(indication, "indication_types", None)
    classifications_relation = getattr(indication, "classifications", None)
    classifications = _serialize_relation_items(classifications_relation)
    interventions_relation = getattr(indication, "interventions", None)
    interventions = _serialize_relation_items(interventions_relation)
    return IndicationCatalogDTO.model_validate(
        {
            "id": indication.id,
            "name": indication.name,
            "name_de": getattr(indication, "name_de", ""),
            "name_en": getattr(indication, "name_en", ""),
            "description": indication.description,
            "indication_types": _serialize_relation_items(indication_types_relation),
            "classifications": classifications,
            "interventions": interventions,
        }
    ).model_dump(mode="json")


def _resolve_kb_finding_names(
    examination: Any, *, module_name: str, version: str | None = None
) -> Optional[Set[str]]:
    lookup = findings_routes._kb_lookup(module_name, version=version)
    exam_entry = lookup["examination"].get(findings_routes._norm_name(examination.name))
    if not exam_entry:
        return None
    finding_names = exam_entry.get("findings", [])
    if not isinstance(finding_names, list):
        return None
    return {findings_routes._norm_name(name) for name in finding_names}


def _resolve_exam_kb_indication_names(
    examination: Any, *, module_name: str, version: str | None = None
) -> Optional[Set[str]]:
    lookup = findings_routes._kb_lookup(module_name, version=version)
    exam_entry = lookup["examination"].get(findings_routes._norm_name(examination.name))
    if not exam_entry:
        return None
    indication_names = exam_entry.get("indications", [])
    if not isinstance(indication_names, list):
        return None
    return {findings_routes._norm_name(name) for name in indication_names}


def _serialize_examination_node_for_indication_tree(
    examination: Any, allowed_finding_names: Optional[Set[str]] = None
) -> Dict[str, Any]:
    findings = list(examination.get_available_findings())
    if allowed_finding_names is not None:
        findings = [
            finding
            for finding in findings
            if findings_routes._norm_name(finding.name) in allowed_finding_names
        ]
    localized_examination = LocalizedCatalogItem.model_validate(
        {
            "id": examination.id,
            "name": examination.name,
            "name_de": getattr(examination, "name_de", ""),
            "name_en": getattr(examination, "name_en", ""),
            "description": getattr(examination, "description", None),
        }
    ).model_dump(mode="json")
    return {
        **localized_examination,
        "findings": [
            {
                "id": finding.id,
                "name": finding.name,
                "description": getattr(finding, "description", None),
            }
            for finding in findings
        ],
    }


def register_indications_routes(
    api: _TypedApi,
    *,
    orm_models: Callable[[], Dict[str, Any]],
    api_error: Callable[[int, str, str], NoReturn],
) -> None:
    @api.get("/examinations/{examination_id}/indications/")
    def indications_by_examination(
        request: BaseRequest,
        examination_id: int,
        module_name: Optional[str] = None,
        module_version: Optional[str] = None,
        patient_examination_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        del request
        try:
            module_name, resolved_version = (
                findings_routes._resolve_catalog_kb_identity(
                    module_name=module_name,
                    module_version=module_version,
                    orm_models=orm_models,
                    patient_examination_id=patient_examination_id,
                    api_error=api_error,
                )
            )
        except RuntimeError as exc:
            api_error(409, "no-active-knowledge-base", str(exc))
        examination_model = orm_models()["Examination"]
        examination = examination_model.objects.filter(id=examination_id).first()
        if not examination:
            api_error(404, "not-found", f"Examination '{examination_id}' not found.")

        assert examination is not None
        if patient_examination_id is not None:
            patient_examination_model = orm_models()["PatientExamination"]
            patient_examination = patient_examination_model.objects.filter(
                id=patient_examination_id
            ).first()
            if not patient_examination:
                api_error(
                    404,
                    "not-found",
                    f"PatientExamination '{patient_examination_id}' not found.",
                )
            assert patient_examination is not None
            if patient_examination.examination_id != examination.id:
                api_error(
                    404,
                    "not-found",
                    "Patient examination "
                    f"'{patient_examination_id}' does not belong to "
                    f"examination '{examination_id}'.",
                )

        indications = _relation_items(getattr(examination, "indications", None))
        kb_allowed_indication_names = _resolve_exam_kb_indication_names(
            examination, module_name=module_name, version=resolved_version
        )
        if kb_allowed_indication_names is not None:
            indications = [
                indication
                for indication in indications
                if findings_routes._norm_name(indication.name)
                in kb_allowed_indication_names
            ]
        return [_serialize_indication(indication) for indication in indications]

    @api.get("/indications/tree/")
    def indications_tree(
        request: BaseRequest,
        module_name: Optional[str] = None,
        module_version: Optional[str] = None,
        patient_examination_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        del request
        try:
            module_name, resolved_version = (
                findings_routes._resolve_catalog_kb_identity(
                    module_name=module_name,
                    module_version=module_version,
                    orm_models=orm_models,
                    patient_examination_id=patient_examination_id,
                    api_error=api_error,
                )
            )
        except RuntimeError as exc:
            api_error(409, "no-active-knowledge-base", str(exc))

        examination_model = orm_models()["Examination"]
        if patient_examination_id is not None:
            patient_examination_model = orm_models()["PatientExamination"]
            patient_examination = patient_examination_model.objects.filter(
                id=patient_examination_id
            ).first()
            if not patient_examination:
                api_error(
                    404,
                    "not-found",
                    f"PatientExamination '{patient_examination_id}' not found.",
                )
            assert patient_examination is not None
            examinations = [getattr(patient_examination, "examination", None)]
            if examinations[0] is None:
                api_error(
                    404,
                    "not-found",
                    f"PatientExamination '{patient_examination_id}' is invalid.",
                )
        else:
            examinations = list(examination_model.objects.all())

        indication_nodes: Dict[int, Dict[str, Any]] = {}
        for examination in examinations:
            if examination is None:
                continue
            allowed_indication_names = _resolve_exam_kb_indication_names(
                examination, module_name=module_name, version=resolved_version
            )
            allowed_finding_names = _resolve_kb_finding_names(
                examination, module_name=module_name, version=resolved_version
            )
            examination_indications = _relation_items(
                getattr(examination, "indications", None)
            )
            if not examination_indications:
                continue
            for indication in examination_indications:
                if (
                    allowed_indication_names is not None
                    and findings_routes._norm_name(indication.name)
                    not in allowed_indication_names
                ):
                    continue
                node = indication_nodes.get(indication.id)
                if node is None:
                    node = _serialize_indication(indication)
                    node["examinations"] = []
                    indication_nodes[indication.id] = node
                node["examinations"].append(
                    _serialize_examination_node_for_indication_tree(
                        examination,
                        allowed_finding_names=allowed_finding_names,
                    )
                )

        return list(indication_nodes.values())
