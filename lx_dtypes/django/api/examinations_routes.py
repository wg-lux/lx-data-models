from __future__ import annotations

from collections.abc import Callable
from typing import Any, NoReturn, Protocol, TypeVar

from lx_dtypes.models.contracts.terminology_catalog import ExaminationCatalogDTO

from .findings_routes import (
    _findings_module_name,
    _norm_name,
    _resolve_exam_kb_finding_names,
    _resolve_kb_finding_classification_names,
    _serialize_finding,
)
from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...


def _serialize_examination(examination: Any, *, module_name: str) -> dict[str, Any]:
    findings = list(examination.get_available_findings())
    kb_allowed_finding_names = _resolve_exam_kb_finding_names(
        examination, module_name=module_name
    )
    findings = [
        finding
        for finding in findings
        if _norm_name(finding.name) in kb_allowed_finding_names
    ]

    examination_types_relation = getattr(examination, "examination_types", None)
    examination_types_items = (
        examination_types_relation.all()
        if examination_types_relation is not None
        and hasattr(examination_types_relation, "all")
        else examination_types_relation or []
    )

    return ExaminationCatalogDTO.model_validate(
        {
            "id": examination.id,
            "name": examination.name,
            "name_de": getattr(examination, "name_de", ""),
            "name_en": getattr(examination, "name_en", ""),
            "description": getattr(examination, "description", None),
            "findings": [
                _serialize_finding(
                    finding,
                    allowed_classification_names=_resolve_kb_finding_classification_names(
                        finding, module_name=module_name
                    ),
                    required_classification_names=set(),
                )
                for finding in findings
            ],
            "examination_types": [
                {
                    "id": examination_type.id,
                    "name": examination_type.name,
                    "name_de": getattr(examination_type, "name_de", ""),
                    "name_en": getattr(examination_type, "name_en", ""),
                    "description": getattr(examination_type, "description", None),
                }
                for examination_type in examination_types_items
            ],
        }
    ).model_dump(mode="json")


def register_examinations_routes(
    api: _TypedApi,
    *,
    orm_models: Callable[[], dict[str, Any]],
    api_error: Callable[[int, str, str], NoReturn],
) -> None:
    @api.get("/examinations/")
    def examinations_catalog(request: BaseRequest) -> list[dict[str, Any]]:
        del request
        module_name = _findings_module_name()
        examination_model = orm_models()["Examination"]
        examinations = examination_model.objects.all().order_by("id")
        return [
            _serialize_examination(examination, module_name=module_name)
            for examination in examinations
        ]

    @api.get("/examinations/{examination_id}/")
    def examination_detail(request: BaseRequest, examination_id: int) -> dict[str, Any]:
        del request
        module_name = _findings_module_name()
        examination_model = orm_models()["Examination"]
        examination = examination_model.objects.filter(id=examination_id).first()
        if not examination:
            api_error(404, "not-found", f"Examination '{examination_id}' not found.")
        assert examination is not None
        return _serialize_examination(examination, module_name=module_name)
