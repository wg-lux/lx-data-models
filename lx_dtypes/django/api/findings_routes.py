from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    NoReturn,
    Protocol,
    TypeVar,
    cast,
)

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone
from pydantic import BaseModel, Field

from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])

if TYPE_CHECKING:
    Schema = BaseModel
else:
    from ninja import Schema


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...

    def post(self, path: str, /) -> _RouteDecorator: ...

    def patch(self, path: str, /) -> _RouteDecorator: ...

    def delete(self, path: str, /) -> _RouteDecorator: ...


class PatientFindingClassificationInput(Schema):
    classification: int
    choice: int


class PatientFindingCreateRequest(Schema):
    patient_examination: int
    finding: int
    classifications: list[PatientFindingClassificationInput] = Field(
        default_factory=list
    )


class PatientFindingUpdateRequest(Schema):
    finding: int | None = None
    is_active: bool | None = None
    classifications: list[PatientFindingClassificationInput] | None = None


class PatientFindingClassificationsRequest(Schema):
    classifications: list[PatientFindingClassificationInput] = Field(
        default_factory=list
    )
    replace: bool = True


_LOAD_MODULE_KB: Callable[..., Any] | None = None


def clear_findings_route_caches() -> None:
    _kb_core_concepts_by_identity.cache_clear()
    _kb_lookup_by_identity.cache_clear()


def _set_load_module_kb(load_module_kb: Callable[..., Any]) -> None:
    global _LOAD_MODULE_KB
    _LOAD_MODULE_KB = load_module_kb


def _require_load_module_kb() -> Callable[..., Any]:
    if _LOAD_MODULE_KB is None:
        raise RuntimeError("findings routes are not initialized with a KB loader")
    return _LOAD_MODULE_KB


def _runtime_descriptor_payloads_from_mapping(
    value: object, *, parent_choice_ref: str
) -> list[dict[str, object]]:
    if not isinstance(value, dict):
        return []

    payloads: list[dict[str, object]] = []
    for descriptor_name, descriptor_value in value.items():
        normalized_name = str(descriptor_name or "").strip()
        if not normalized_name:
            continue
        if not isinstance(descriptor_value, (str, int, float, bool, list)):
            continue
        payloads.append(
            {
                "classification_choice_descriptor": normalized_name,
                "descriptor_value": descriptor_value,
                "patient_finding_classification_choice": parent_choice_ref,
            }
        )
    return payloads


def _as_str_list_from_relation(relation: object) -> list[str]:
    if relation is None:
        return []
    if hasattr(relation, "all"):
        return [str(getattr(item, "pk", item)) for item in relation.all()]  # type: ignore[misc]
    if isinstance(relation, list):
        return [str(item) for item in relation]
    return [str(relation)]


def _findings_module_name() -> str:
    """Resolve the active module only for legacy, non-examination discovery routes."""

    from .terminology_routes import active_terminology_selection

    active = active_terminology_selection()
    if active is None:
        raise RuntimeError("No active knowledge-base bundle is selected.")
    return active[0]


class PatientExaminationKnowledgeBaseIdentityError(RuntimeError):
    """Raised when an examination-bound route has no complete persisted identity."""


def _resolve_exam_kb_identity(patient_examination: Any) -> tuple[str, str]:
    module_name = str(
        getattr(patient_examination, "knowledge_base_module", "") or ""
    ).strip()
    version = str(
        getattr(patient_examination, "knowledge_base_version", "") or ""
    ).strip()
    if bool(module_name) != bool(version):
        raise PatientExaminationKnowledgeBaseIdentityError(
            "PatientExamination knowledge-base identity is incomplete."
        )
    if module_name and version:
        return module_name, version
    raise PatientExaminationKnowledgeBaseIdentityError(
        "PatientExamination requires an explicit knowledge-base identity."
    )


def _resolve_catalog_kb_identity(
    module_name: str | None,
    module_version: str | None,
    orm_models: Callable[[], dict[str, Any]],
    patient_examination_id: int | None,
    api_error: Callable[[int, str, str], NoReturn],
) -> tuple[str, str | None]:
    requested_module_name = str(module_name or "").strip()
    requested_module_version = str(module_version or "").strip()
    if requested_module_name:
        if not requested_module_version:
            api_error(
                409,
                "knowledge-base-identity-required",
                "module_version is required when module_name is supplied.",
            )

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
            pinned_module = str(
                getattr(patient_examination, "knowledge_base_module", "") or ""
            ).strip()
            pinned_version = str(
                getattr(patient_examination, "knowledge_base_version", "") or ""
            ).strip()
            if (
                pinned_module != requested_module_name
                or pinned_version != requested_module_version
            ):
                api_error(
                    409,
                    "knowledge-base-identity-conflict",
                    "Requested knowledge-base identity does not match the "
                    f"PatientExamination '{patient_examination_id}' identity.",
                )

        return requested_module_name, requested_module_version

    if requested_module_version:
        api_error(
            409,
            "knowledge-base-identity-required",
            "module_name is required when module_version is supplied.",
        )

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
        return _resolve_exam_kb_identity(patient_examination)

    from .terminology_routes import active_terminology_selection

    active = active_terminology_selection()
    if active is None:
        raise RuntimeError("No active knowledge-base bundle is selected.")
    return active


def _norm_name(value: str | None) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


@lru_cache(maxsize=8)
def _kb_core_concepts_by_identity(
    module_name: str,
    version: str,
) -> dict[str, Any]:
    loader = _require_load_module_kb()
    return cast(
        dict[str, Any],
        loader(module_name, version=version).export_core_concepts(),
    )


def _build_kb_lookup(core: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    examination_by_name = {
        _norm_name(item.get("name")): item for item in core.get("examination", [])
    }
    finding_by_name = {
        _norm_name(item.get("name")): item for item in core.get("finding", [])
    }
    classification_by_name = {
        _norm_name(item.get("name")): item for item in core.get("classification", [])
    }
    choice_by_name = {
        _norm_name(item.get("name")): item
        for item in core.get("classification_choice", [])
    }
    indication_by_name = {
        _norm_name(item.get("name")): item for item in core.get("indication", [])
    }
    return {
        "examination": examination_by_name,
        "finding": finding_by_name,
        "classification": classification_by_name,
        "classification_choice": choice_by_name,
        "indication": indication_by_name,
    }


def _kb_core_concepts(module_name: str) -> dict[str, Any]:
    loader = _require_load_module_kb()
    kb = loader(module_name)
    version = str(getattr(getattr(kb, "config", None), "version", "") or "").strip()
    if not version:
        return cast(dict[str, Any], kb.export_core_concepts())
    return _kb_core_concepts_by_identity(module_name, version)


@lru_cache(maxsize=8)
def _kb_lookup_by_identity(
    module_name: str,
    version: str,
) -> dict[str, dict[str, dict[str, Any]]]:
    core = _kb_core_concepts_by_identity(module_name, version)
    return _build_kb_lookup(core)


def _kb_lookup(
    module_name: str, version: str | None = None
) -> dict[str, dict[str, dict[str, Any]]]:
    if version:
        return _kb_lookup_by_identity(module_name, version)

    loader = _require_load_module_kb()
    kb = loader(module_name)
    version = str(getattr(getattr(kb, "config", None), "version", "") or "").strip()
    if not version:
        return _build_kb_lookup(cast(dict[str, Any], kb.export_core_concepts()))
    return _kb_lookup_by_identity(module_name, version)


def _active_patient_findings_queryset(
    orm_models: Callable[[], dict[str, Any]],
) -> QuerySet[Any]:
    patient_finding_model = orm_models()["PatientFinding"]
    return cast(
        QuerySet[Any],
        patient_finding_model.objects.filter(is_active=True).select_related(
            "patient_examination", "finding"
        ),
    )


def build_p_examination_payload_from_host_ledger(
    patient_examination: object,
    *,
    route_module_name: str,
    orm_models: Callable[[], dict[str, Any]],
    active_patient_findings_queryset: Callable[[], Any] | None = None,
) -> PExamination:
    patient_examination_id = getattr(patient_examination, "id", None)
    if patient_examination_id is None:
        raise ValueError("PatientExamination is missing an id.")

    examination_obj = getattr(patient_examination, "examination_safe", None) or getattr(
        patient_examination, "examination", None
    )
    examination_name = str(getattr(examination_obj, "name", "") or "").strip()
    if not examination_name:
        raise ValueError(
            f"PatientExamination '{patient_examination_id}' is missing examination name."
        )

    patient_value = getattr(patient_examination, "patient_id", None)
    if patient_value is None:
        patient_obj = getattr(patient_examination, "patient", None)
        patient_value = getattr(patient_obj, "pk", None)
    patient_token = str(
        patient_value or f"patient_examination_{patient_examination_id}"
    )

    module_from_ledger = str(
        getattr(patient_examination, "knowledge_base_module", "") or ""
    ).strip()
    version_from_ledger = str(
        getattr(patient_examination, "knowledge_base_version", "") or ""
    ).strip()

    queryset_provider = (
        active_patient_findings_queryset
        if active_patient_findings_queryset is not None
        else lambda: _active_patient_findings_queryset(orm_models)
    )
    patient_findings_qs = queryset_provider().filter(
        patient_examination_id=patient_examination_id
    )
    patient_findings_payload: list[dict[str, object]] = []
    for patient_finding in patient_findings_qs:
        finding_name = str(getattr(patient_finding.finding, "name", "") or "").strip()
        if not finding_name:
            continue

        classifications_payload: list[dict[str, object]] = []
        active_classifications = (
            patient_finding.classifications.filter(is_active=True)
            .select_related("classification", "classification_choice")
            .all()
        )
        for index, item in enumerate(active_classifications):
            classification_name = str(
                getattr(item.classification, "name", "") or ""
            ).strip()
            choice_name = str(
                getattr(item.classification_choice, "name", "") or ""
            ).strip()
            if not classification_name:
                continue
            if not choice_name:
                choice_name = classification_name

            choice_ref = f"pe_{patient_examination_id}_pf_{patient_finding.id}_choice_{index + 1}"
            classifications_payload.append(
                {
                    "classification": classification_name,
                    "classification_choice": choice_name,
                    "patient_finding_classifications": str(item.id),
                    "patient_finding_classification_choice_descriptors": (
                        _runtime_descriptor_payloads_from_mapping(
                            getattr(item, "numerical_descriptors", {}),
                            parent_choice_ref=choice_ref,
                        )
                    ),
                }
            )

        interventions_payload: list[dict[str, object]] = []
        active_interventions = (
            patient_finding.interventions.filter(is_active=True)
            .select_related("intervention")
            .all()
        )
        for item in active_interventions:
            intervention_name = str(
                getattr(item.intervention, "name", "") or ""
            ).strip()
            if not intervention_name:
                continue
            interventions_payload.append(
                {
                    "patient_finding_interventions": str(item.id),
                    "intervention": intervention_name,
                }
            )

        patient_findings_payload.append(
            {
                "finding": finding_name,
                "patient_examination": examination_name,
                "patient_finding_classifications": [
                    {
                        "patient_finding": str(patient_finding.id),
                        "patient_finding_classification_choices": classifications_payload,
                    }
                ]
                if classifications_payload
                else [],
                "patient_finding_interventions": [
                    {
                        "patient_finding": str(patient_finding.id),
                        "patient_finding_interventions": interventions_payload,
                    }
                ]
                if interventions_payload
                else [],
            }
        )

    payload = {
        "patient": patient_token,
        "examiners": _as_str_list_from_relation(
            getattr(patient_examination, "examiners", None)
        ),
        "examination": examination_name,
        "knowledge_base_module": module_from_ledger or route_module_name,
        "knowledge_base_version": version_from_ledger or None,
        "patient_findings": patient_findings_payload,
    }
    return PExamination.model_validate(payload)


def _serialize_choice(choice: Any) -> dict[str, Any]:
    return {
        "id": choice.id,
        "name": choice.name,
        "description": choice.description,
        "subcategories": choice.subcategories,
        "numerical_descriptors": choice.numerical_descriptors,
    }


def _serialize_classification(
    classification: Any, *, required: bool = False
) -> dict[str, Any]:
    choices = classification.choices.all()
    classification_types = [
        _norm_name(c_type.name) for c_type in classification.classification_types.all()
    ]
    return {
        "id": classification.id,
        "name": classification.name,
        "description": classification.description,
        "required": required,
        "classification_types": classification_types,
        "choices": [_serialize_choice(choice) for choice in choices],
    }


def _split_classifications(
    classifications: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    location: list[dict[str, Any]] = []
    morphology: list[dict[str, Any]] = []
    for classification in classifications:
        c_types = {
            _norm_name(v) for v in classification.get("classification_types", [])
        }
        if "location" in c_types:
            location.append(classification)
        if "morphology" in c_types:
            morphology.append(classification)
    return {
        "location_classifications": location,
        "morphology_classifications": morphology,
    }


def _serialize_finding(
    finding: Any,
    *,
    allowed_classification_names: set[str] | None = None,
    required_classification_names: set[str] | None = None,
) -> dict[str, Any]:
    all_classifications = finding.finding_classifications.all().prefetch_related(
        "choices", "classification_types"
    )
    selected_classifications = []
    for classification in all_classifications:
        c_name = _norm_name(classification.name)
        if (
            allowed_classification_names is not None
            and c_name not in allowed_classification_names
        ):
            continue
        selected_classifications.append(
            _serialize_classification(
                classification,
                required=(
                    required_classification_names is not None
                    and c_name in required_classification_names
                ),
            )
        )
    split = _split_classifications(selected_classifications)
    return {
        "id": finding.id,
        "name": finding.name,
        "description": finding.description,
        "classifications": selected_classifications,
        "location_classifications": split["location_classifications"],
        "morphology_classifications": split["morphology_classifications"],
        "FindingClassifications": selected_classifications,
    }


def _serialize_patient_finding_classification(
    item: Any,
) -> dict[str, Any]:
    return {
        "id": item.id,
        "classification": item.classification_id,
        "classification_choice": item.classification_choice_id,
        "classification_name": item.classification.name,
        "classification_choice_name": item.classification_choice.name,
        "subcategories": item.subcategories,
        "numerical_descriptors": item.numerical_descriptors,
        "is_active": item.is_active,
    }


def _serialize_patient_finding(item: Any) -> dict[str, Any]:
    classifications = item.classifications.filter(is_active=True).select_related(
        "classification", "classification_choice"
    )
    return {
        "id": item.id,
        "patient_examination": item.patient_examination_id,
        "finding": item.finding_id,
        "is_active": item.is_active,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "classifications": [
            _serialize_patient_finding_classification(classification)
            for classification in classifications
        ],
    }


def _resolve_exam_kb_finding_names(
    examination: Any, *, module_name: str, version: str | None = None
) -> set[str]:
    lookup = _kb_lookup(module_name, version=version)
    exam_entry = lookup["examination"].get(_norm_name(examination.name))
    if not exam_entry:
        return set()
    finding_names = exam_entry.get("findings", [])
    if not isinstance(finding_names, list):
        return set()
    return {_norm_name(name) for name in finding_names}


def _resolve_kb_finding_classification_names(
    finding: Any, *, module_name: str, version: str | None = None
) -> set[str]:
    lookup = _kb_lookup(module_name, version=version)
    finding_entry = lookup["finding"].get(_norm_name(finding.name))
    if not finding_entry:
        return set()
    classifications = finding_entry.get("classifications", [])
    if not isinstance(classifications, list):
        return set()
    return {_norm_name(name) for name in classifications}


def _resolve_kb_classification_choice_names(
    classification: Any, *, module_name: str, version: str | None = None
) -> set[str]:
    lookup = _kb_lookup(module_name, version=version)
    classification_entry = lookup["classification"].get(_norm_name(classification.name))
    if not classification_entry:
        return set()
    choices = classification_entry.get("classification_choices", [])
    if not isinstance(choices, list):
        return set()
    return {_norm_name(name) for name in choices}


def _validate_finding_for_examination(
    finding: Any,
    patient_examination: Any,
    *,
    module_name: str,
    version: str | None = None,
    api_error: Callable[[int, str, str], NoReturn],
) -> None:
    available_findings = patient_examination.examination_safe.get_available_findings()
    if finding not in available_findings:
        api_error(
            400,
            "invalid-finding",
            f"Finding '{finding.name}' is not allowed for examination '{patient_examination.examination_safe.name}'.",
        )

    kb_allowed_names = _resolve_exam_kb_finding_names(
        patient_examination.examination_safe, module_name=module_name, version=version
    )
    if _norm_name(finding.name) not in kb_allowed_names:
        api_error(
            400,
            "invalid-finding",
            f"Finding '{finding.name}' is not present in dtypes module '{module_name}' for examination '{patient_examination.examination_safe.name}'.",
        )


def _validate_classification_payload(
    *,
    finding: Any,
    classification: Any,
    choice: Any,
    module_name: str,
    version: str | None = None,
    api_error: Callable[[int, str, str], NoReturn],
) -> None:
    if not finding.finding_classifications.filter(id=classification.id).exists():
        api_error(
            400,
            "invalid-choice",
            f"Classification '{classification.name}' is not valid for finding '{finding.name}'.",
        )
    if not classification.choices.filter(id=choice.id).exists():
        api_error(
            400,
            "invalid-choice",
            f"Choice '{choice.name}' is not valid for classification '{classification.name}'.",
        )

    kb_classifications = _resolve_kb_finding_classification_names(
        finding, module_name=module_name, version=version
    )
    if _norm_name(classification.name) not in kb_classifications:
        api_error(
            400,
            "invalid-choice",
            f"Classification '{classification.name}' is not defined in dtypes for finding '{finding.name}'.",
        )

    kb_choices = _resolve_kb_classification_choice_names(
        classification, module_name=module_name, version=version
    )
    if _norm_name(choice.name) not in kb_choices:
        api_error(
            400,
            "invalid-choice",
            f"Choice '{choice.name}' is not defined in dtypes for classification '{classification.name}'.",
        )


def _replace_patient_finding_classifications(
    patient_finding: Any,
    entries: list[PatientFindingClassificationInput],
    *,
    module_name: str,
    version: str | None = None,
    orm_models: Callable[[], dict[str, Any]],
    api_error: Callable[[int, str, str], NoReturn],
) -> None:
    patient_finding.classifications.all().delete()
    finding_classification_model = orm_models()["FindingClassification"]
    finding_classification_choice_model = orm_models()["FindingClassificationChoice"]
    patient_finding_classification_model = orm_models()["PatientFindingClassification"]
    for entry in entries:
        classification = finding_classification_model.objects.filter(
            id=entry.classification
        ).first()
        if not classification:
            api_error(
                400,
                "invalid-choice",
                f"Classification id '{entry.classification}' does not exist.",
            )
        choice = finding_classification_choice_model.objects.filter(
            id=entry.choice
        ).first()
        if not choice:
            api_error(
                400,
                "invalid-choice",
                f"Classification choice id '{entry.choice}' does not exist.",
            )
        assert classification is not None
        assert choice is not None
        _validate_classification_payload(
            finding=patient_finding.finding,
            classification=classification,
            choice=choice,
            module_name=module_name,
            version=version,
            api_error=api_error,
        )
        patient_finding_classification_model.objects.create(
            finding=patient_finding,
            classification=classification,
            classification_choice=choice,
            is_active=True,
        )


def _get_or_create_active_patient_finding_classification(
    patient_finding: Any,
    *,
    classification: Any,
    choice: Any,
    orm_models: Callable[[], dict[str, Any]],
) -> Any:
    existing = patient_finding.classifications.filter(
        classification=classification,
        classification_choice=choice,
        is_active=True,
    ).first()
    if existing is not None:
        return existing
    patient_finding_classification_model = orm_models()["PatientFindingClassification"]
    return patient_finding_classification_model.objects.create(
        finding=patient_finding,
        classification=classification,
        classification_choice=choice,
        is_active=True,
    )


def register_findings_routes(
    api: _TypedApi,
    *,
    load_module_kb: Callable[..., Any],
    orm_models: Callable[[], dict[str, Any]],
    api_error: Callable[[int, str, str], NoReturn],
    authenticate_request_user: Callable[[BaseRequest], Any | None],
    patient_examination_access_allowed: Callable[[BaseRequest, object], bool],
    patient_finding_access_allowed: Callable[[BaseRequest, object], bool],
    patient_findings_queryset_for_request: Callable[[BaseRequest], Any],
    build_p_examination_payload_from_host_ledger: Callable[..., PExamination]
    | None = None,
    persist_patient_examination_dtypes_record: Callable[
        [object, PExamination], dict[str, Any]
    ]
    | None = None,
) -> None:
    _set_load_module_kb(load_module_kb)

    def require_authenticated_actor(request: BaseRequest) -> Any:
        actor = authenticate_request_user(request)
        if actor is None:
            api_error(401, "authentication-required", "Authentication is required.")
        return actor

    def require_patient_finding_access(
        request: BaseRequest, patient_finding: object, patient_finding_id: int
    ) -> None:
        if not patient_finding_access_allowed(request, patient_finding):
            api_error(
                404,
                "not-found",
                f"Patient finding '{patient_finding_id}' not found.",
            )

    def refresh_patient_examination_dtypes_record(patient_examination: object) -> None:
        if (
            build_p_examination_payload_from_host_ledger is None
            or persist_patient_examination_dtypes_record is None
        ):
            return
        try:
            module_name_for_record, _ = _resolve_exam_kb_identity(patient_examination)
        except PatientExaminationKnowledgeBaseIdentityError as exc:
            api_error(409, "knowledge-base-identity-required", str(exc))
        payload = build_p_examination_payload_from_host_ledger(
            patient_examination,
            route_module_name=module_name_for_record,
        )
        persist_patient_examination_dtypes_record(patient_examination, payload)

    @api.get("/core-concepts/{module_name}")
    def core_concepts_by_module(
        request: BaseRequest, module_name: str
    ) -> dict[str, Any]:
        """
        Return canonical core concept payloads for one KB module.
        """
        del request
        kb = load_module_kb(module_name)
        payload = cast(dict[str, Any], kb.export_core_concepts())
        config = getattr(kb, "config", None)
        payload["knowledge_base_module"] = str(
            getattr(config, "name", module_name) or module_name
        ).strip()
        payload["knowledge_base_version"] = (
            str(getattr(config, "version", "") or "").strip() or None
        )
        return payload

    @api.get("/examinations/{examination_id}/findings/")
    def findings_by_examination(
        request: BaseRequest,
        examination_id: int,
        module_name: str | None = None,
        module_version: str | None = None,
        patient_examination_id: int | None = None,
    ) -> list[dict[str, Any]]:
        del request
        try:
            module_name, resolved_version = _resolve_catalog_kb_identity(
                module_name=module_name,
                module_version=module_version,
                orm_models=orm_models,
                patient_examination_id=patient_examination_id,
                api_error=api_error,
            )
        except PatientExaminationKnowledgeBaseIdentityError as exc:
            api_error(409, "knowledge-base-identity-required", str(exc))
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
        findings = list(examination.get_available_findings())
        kb_allowed_finding_names = _resolve_exam_kb_finding_names(
            examination, module_name=module_name, version=resolved_version
        )
        findings = [
            finding
            for finding in findings
            if _norm_name(finding.name) in kb_allowed_finding_names
        ]

        response = []
        for finding in findings:
            kb_allowed_classifications = _resolve_kb_finding_classification_names(
                finding, module_name=module_name, version=resolved_version
            )
            response.append(
                _serialize_finding(
                    finding,
                    allowed_classification_names=kb_allowed_classifications,
                    required_classification_names=set(),
                )
            )
        return response

    @api.get("/findings/{finding_id}/classifications/")
    def classifications_by_finding(
        request: BaseRequest,
        finding_id: int,
        module_name: str | None = None,
        module_version: str | None = None,
        patient_examination_id: int | None = None,
    ) -> list[dict[str, Any]]:
        del request
        try:
            module_name, resolved_version = _resolve_catalog_kb_identity(
                module_name=module_name,
                module_version=module_version,
                orm_models=orm_models,
                patient_examination_id=patient_examination_id,
                api_error=api_error,
            )
        except PatientExaminationKnowledgeBaseIdentityError as exc:
            api_error(409, "knowledge-base-identity-required", str(exc))
        except RuntimeError as exc:
            api_error(409, "no-active-knowledge-base", str(exc))
        finding_model = orm_models()["Finding"]
        finding = finding_model.objects.filter(id=finding_id).first()
        if not finding:
            api_error(404, "not-found", f"Finding '{finding_id}' not found.")
        assert finding is not None

        kb_allowed_classifications = _resolve_kb_finding_classification_names(
            finding, module_name=module_name, version=resolved_version
        )
        serialized = _serialize_finding(
            finding,
            allowed_classification_names=kb_allowed_classifications,
            required_classification_names=set(),
        )
        return cast(list[dict[str, Any]], serialized["classifications"])

    @api.get("/classifications/{classification_id}/choices/")
    def choices_by_classification(
        request: BaseRequest,
        classification_id: int,
        module_name: str | None = None,
        module_version: str | None = None,
        patient_examination_id: int | None = None,
    ) -> dict[str, Any]:
        del request
        try:
            module_name, resolved_version = _resolve_catalog_kb_identity(
                module_name=module_name,
                module_version=module_version,
                orm_models=orm_models,
                patient_examination_id=patient_examination_id,
                api_error=api_error,
            )
        except PatientExaminationKnowledgeBaseIdentityError as exc:
            api_error(409, "knowledge-base-identity-required", str(exc))
        except RuntimeError as exc:
            api_error(409, "no-active-knowledge-base", str(exc))
        finding_classification_model = orm_models()["FindingClassification"]
        classification = finding_classification_model.objects.filter(
            id=classification_id
        ).first()
        if not classification:
            api_error(
                404, "not-found", f"Classification '{classification_id}' not found."
            )
        assert classification is not None

        kb_allowed_choices = _resolve_kb_classification_choice_names(
            classification, module_name=module_name, version=resolved_version
        )
        all_choices = list(classification.choices.all())
        all_choices = [
            choice
            for choice in all_choices
            if _norm_name(choice.name) in kb_allowed_choices
        ]
        return {"choices": [_serialize_choice(choice) for choice in all_choices]}

    @api.get("/patient-findings/")
    def list_patient_findings(
        request: BaseRequest, patient_examination: int | None = None
    ) -> list[dict[str, Any]]:
        require_authenticated_actor(request)
        queryset = patient_findings_queryset_for_request(request)
        if patient_examination is not None:
            queryset = queryset.filter(patient_examination_id=patient_examination)
        return [_serialize_patient_finding(item) for item in queryset]

    @api.post("/patient-findings/")
    def create_patient_finding(
        request: BaseRequest, payload: PatientFindingCreateRequest
    ) -> dict[str, Any]:
        require_authenticated_actor(request)
        patient_examination_model = orm_models()["PatientExamination"]
        finding_model = orm_models()["Finding"]
        patient_finding_model = orm_models()["PatientFinding"]
        patient_examination = patient_examination_model.objects.filter(
            id=payload.patient_examination
        ).first()
        if not patient_examination:
            api_error(
                404,
                "not-found",
                f"PatientExamination '{payload.patient_examination}' not found.",
            )
        assert patient_examination is not None
        if not patient_examination_access_allowed(request, patient_examination):
            api_error(
                404,
                "not-found",
                f"PatientExamination '{payload.patient_examination}' not found.",
            )
        module_name, module_version = _resolve_exam_kb_identity(patient_examination)

        finding = finding_model.objects.filter(id=payload.finding).first()
        if not finding:
            api_error(404, "not-found", f"Finding '{payload.finding}' not found.")
        assert finding is not None

        _validate_finding_for_examination(
            finding=finding,
            patient_examination=patient_examination,
            module_name=module_name,
            version=module_version,
            api_error=api_error,
        )

        try:
            with transaction.atomic():
                patient_finding = patient_finding_model.objects.create(
                    patient_examination=patient_examination,
                    finding=finding,
                )
                if payload.classifications:
                    _replace_patient_finding_classifications(
                        patient_finding,
                        payload.classifications,
                        module_name=module_name,
                        version=module_version,
                        orm_models=orm_models,
                        api_error=api_error,
                    )
                refresh_patient_examination_dtypes_record(patient_examination)
                return _serialize_patient_finding(patient_finding)
        except IntegrityError as exc:
            if "unique_active_finding_per_examination" in str(exc):
                api_error(
                    400,
                    "duplicate-finding",
                    f"Finding '{finding.name}' is already active for this patient examination.",
                )
            raise
        except ValidationError as exc:
            message = str(exc)
            normalized_message = message.lower()
            if "erforderliche findings fehlen" in normalized_message:
                code = "required-finding"
            elif (
                "unique_active_finding_per_examination" in normalized_message
                or "already exists" in normalized_message
                or "bereits" in normalized_message
            ):
                code = "duplicate-finding"
            else:
                code = "invalid-finding"
            api_error(400, code, message)

    @api.patch("/patient-findings/{patient_finding_id}/")
    def patch_patient_finding(
        request: BaseRequest,
        patient_finding_id: int,
        payload: PatientFindingUpdateRequest,
    ) -> dict[str, Any]:
        actor = require_authenticated_actor(request)
        patient_finding = (
            patient_findings_queryset_for_request(request)
            .filter(id=patient_finding_id)
            .first()
        )
        if not patient_finding:
            api_error(
                404, "not-found", f"Patient finding '{patient_finding_id}' not found."
            )
        assert patient_finding is not None
        require_patient_finding_access(request, patient_finding, patient_finding_id)
        module_name, module_version = _resolve_exam_kb_identity(
            patient_finding.patient_examination
        )

        with transaction.atomic():
            if payload.finding is not None:
                finding_model = orm_models()["Finding"]
                finding = finding_model.objects.filter(id=payload.finding).first()
                if not finding:
                    api_error(
                        404, "not-found", f"Finding '{payload.finding}' not found."
                    )
                assert finding is not None
                _validate_finding_for_examination(
                    finding=finding,
                    patient_examination=patient_finding.patient_examination,
                    module_name=module_name,
                    version=module_version,
                    api_error=api_error,
                )
                patient_finding.finding = finding

            if payload.is_active is not None:
                if payload.is_active:
                    patient_finding.is_active = True
                    patient_finding.deactivated_at = None
                    patient_finding.deactivated_by = None
                else:
                    patient_finding.is_active = False
                    patient_finding.deactivated_by = actor
                    patient_finding.deactivated_at = timezone.now()

            patient_finding.save()

            if payload.classifications is not None:
                _replace_patient_finding_classifications(
                    patient_finding,
                    payload.classifications,
                    module_name=module_name,
                    version=module_version,
                    orm_models=orm_models,
                    api_error=api_error,
                )
            refresh_patient_examination_dtypes_record(
                patient_finding.patient_examination
            )

        return _serialize_patient_finding(patient_finding)

    @api.delete("/patient-findings/{patient_finding_id}/")
    def delete_patient_finding(
        request: BaseRequest, patient_finding_id: int
    ) -> dict[str, Any]:
        actor = require_authenticated_actor(request)

        patient_finding = (
            patient_findings_queryset_for_request(request)
            .filter(id=patient_finding_id)
            .first()
        )
        if not patient_finding:
            api_error(
                404, "not-found", f"Patient finding '{patient_finding_id}' not found."
            )
        assert patient_finding is not None
        require_patient_finding_access(request, patient_finding, patient_finding_id)

        with transaction.atomic():
            patient_finding.is_active = False
            patient_finding.deactivated_by = actor
            patient_finding.deactivated_at = timezone.now()
            patient_finding.save(
                update_fields=["is_active", "deactivated_at", "deactivated_by"]
            )
            refresh_patient_examination_dtypes_record(
                patient_finding.patient_examination
            )
        return {"success": True, "id": patient_finding_id}

    @api.post("/patient-findings/{patient_finding_id}/classifications/")
    def set_patient_finding_classifications(
        request: BaseRequest,
        patient_finding_id: int,
        payload: PatientFindingClassificationsRequest,
    ) -> dict[str, Any]:
        require_authenticated_actor(request)
        patient_finding = (
            patient_findings_queryset_for_request(request)
            .filter(id=patient_finding_id)
            .first()
        )
        if not patient_finding:
            api_error(
                404, "not-found", f"Patient finding '{patient_finding_id}' not found."
            )
        assert patient_finding is not None
        require_patient_finding_access(request, patient_finding, patient_finding_id)
        module_name, module_version = _resolve_exam_kb_identity(
            patient_finding.patient_examination
        )

        with transaction.atomic():
            finding_classification_model = orm_models()["FindingClassification"]
            finding_classification_choice_model = orm_models()[
                "FindingClassificationChoice"
            ]
            if payload.replace:
                patient_finding.classifications.all().delete()
            for entry in payload.classifications:
                classification = finding_classification_model.objects.filter(
                    id=entry.classification
                ).first()
                if not classification:
                    api_error(
                        400,
                        "invalid-choice",
                        f"Classification id '{entry.classification}' does not exist.",
                    )
                choice = finding_classification_choice_model.objects.filter(
                    id=entry.choice
                ).first()
                if not choice:
                    api_error(
                        400,
                        "invalid-choice",
                        f"Classification choice id '{entry.choice}' does not exist.",
                    )
                assert classification is not None
                assert choice is not None
                _validate_classification_payload(
                    finding=patient_finding.finding,
                    classification=classification,
                    choice=choice,
                    module_name=module_name,
                    version=module_version,
                    api_error=api_error,
                )
                _get_or_create_active_patient_finding_classification(
                    patient_finding,
                    classification=classification,
                    choice=choice,
                    orm_models=orm_models,
                )
            refresh_patient_examination_dtypes_record(
                patient_finding.patient_examination
            )

        return _serialize_patient_finding(patient_finding)
