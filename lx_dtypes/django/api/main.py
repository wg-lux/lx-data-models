from __future__ import annotations

import os
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    NoReturn,
    Optional,
    Protocol,
    Set,
    TypedDict,
    TypeVar,
    cast,
    Literal,
    runtime_checkable,
)

from django.conf import settings
from ninja.errors import HttpError  # type: ignore[import-untyped]

from lx_dtypes.models.contracts import KnowledgeBaseContract
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseVersionNotFoundError,
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
    load_module_config,
)
from lx_dtypes.models.interface import KnowledgeBaseResolver as _knowledge_base_resolver
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

from .findings_routes import (
    PatientFindingClassificationInput,
    build_p_examination_payload_from_host_ledger as _build_payload_from_host_ledger,
    clear_findings_route_caches,
    register_findings_routes,
)
from .indications_routes import register_indications_routes
from .examinations_routes import register_examinations_routes
from .knowledge_base_graph_routes import register_knowledge_base_graph_routes
from .request_types import BaseRequest
from .report_template_routes import register_report_template_routes
from .report_template_builder import (
    ReportTemplateModuleLocation,
    module_dir as report_template_module_dir,
)
from .lookup_tracker import register_runtime_lookup_tracker
from .terminology_routes import (
    active_terminology_selection,
    register_terminology_routes,
)

F = TypeVar("F", bound=Callable[..., Any])
ReportLanguageCode = Literal["de", "en"]


class ReportLanguageOption(TypedDict):
    code: ReportLanguageCode
    label: str


class ReportLanguagesResponse(TypedDict):
    default_language: ReportLanguageCode
    languages: List[ReportLanguageOption]


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    @property
    def urls(self) -> Any: ...

    def get(self, path: str, /) -> _RouteDecorator: ...

    def post(self, path: str, /) -> _RouteDecorator: ...

    def patch(self, path: str, /) -> _RouteDecorator: ...

    def delete(self, path: str, /) -> _RouteDecorator: ...

    def exception_handler(self, exc_class: type[Exception], /) -> _RouteDecorator: ...

    def create_response(self, request: Any, data: Any, *, status: int) -> Any: ...


if TYPE_CHECKING:
    api = cast(_TypedApi, object())
else:
    from ninja import NinjaAPI

    api = cast(_TypedApi, NinjaAPI(urls_namespace="lx_dtypes_base_api"))


@api.get("/reporting/languages")
def reporting_languages(request: BaseRequest) -> ReportLanguagesResponse:
    """Return the report languages supported by LXDM concept labels."""
    del request
    return {
        "default_language": "de",
        "languages": [
            {"code": "de", "label": "Deutsch"},
            {"code": "en", "label": "English"},
        ],
    }


@lru_cache(maxsize=1)
def _host_models_module() -> Any:
    module_path = getattr(settings, "LX_DTYPES_HOST_MODELS_MODULE", None) or os.getenv(
        "LX_DTYPES_HOST_MODELS_MODULE"
    )
    if not module_path:
        raise RuntimeError(
            "LX_DTYPES_HOST_MODELS_MODULE must be configured to use lx_dtypes.django.api."
        )
    return import_module(module_path)


def _host_integration_is_configured() -> bool:
    return bool(
        getattr(settings, "LX_DTYPES_HOST_MODELS_MODULE", None)
        or os.getenv("LX_DTYPES_HOST_MODELS_MODULE")
    )


@lru_cache(maxsize=1)
def _orm_models() -> Dict[str, Any]:
    host_models = _host_models_module()
    return {
        "Examination": getattr(host_models, "Examination"),
        "Finding": getattr(host_models, "Finding"),
        "FindingClassification": getattr(host_models, "FindingClassification"),
        "FindingClassificationChoice": getattr(
            host_models, "FindingClassificationChoice"
        ),
        "PatientExamination": getattr(host_models, "PatientExamination"),
        "PatientFinding": getattr(host_models, "PatientFinding"),
        "PatientFindingClassification": getattr(
            host_models, "PatientFindingClassification"
        ),
    }


def _persist_patient_examination_dtypes_record(
    patient_examination: object,
    payload: PExamination,
) -> dict[str, Any]:
    persist = getattr(
        _host_models_module(), "persist_patient_examination_dtypes_record"
    )
    return cast(dict[str, Any], persist(patient_examination, payload))


def _authenticate_request_user(request: BaseRequest) -> Any | None:
    if not _host_integration_is_configured():
        return None
    authenticate = getattr(_host_models_module(), "authenticate_request_user", None)
    if callable(authenticate):
        return authenticate(request)
    return _request_user_if_authenticated(request)


def _patient_finding_access_allowed(
    request: BaseRequest, patient_finding: object
) -> bool:
    authorize = getattr(_host_models_module(), "patient_finding_access_allowed", None)
    if not callable(authorize):
        return False
    return bool(authorize(request, patient_finding))


def _patient_examination_access_allowed(
    request: BaseRequest, patient_examination: object
) -> bool:
    authorize = getattr(
        _host_models_module(), "patient_examination_access_allowed", None
    )
    if not callable(authorize):
        return False
    return bool(authorize(request, patient_examination))


def _patient_findings_queryset_for_request(request: BaseRequest) -> Any:
    scope_queryset = getattr(
        _host_models_module(), "patient_findings_queryset_for_request", None
    )
    if not callable(scope_queryset):
        return _active_patient_findings_queryset().none()
    return scope_queryset(request)


def _terminology_write_access_allowed(actor: object) -> bool:
    authorize = getattr(_host_models_module(), "terminology_write_access_allowed", None)
    return bool(callable(authorize) and authorize(actor))


def _report_template_access_allowed(
    actor: object,
    capability: Literal["report_template:read", "report_template:write"],
) -> bool:
    if not _host_integration_is_configured():
        return False
    authorize = getattr(_host_models_module(), "report_template_access_allowed", None)
    return bool(callable(authorize) and authorize(actor, capability))


class StructuredApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


@api.exception_handler(StructuredApiError)
def handle_structured_api_error(request: Any, exc: StructuredApiError) -> Any:
    return api.create_response(
        request,
        {"code": exc.code, "message": exc.message},
        status=exc.status_code,
    )


def _resolve_active_version(module_name: str, version: str | None) -> str | None:
    if version:
        return version
    active = active_terminology_selection()
    if active is not None and active[0] == module_name:
        return active[1]
    if active is None:
        raise HttpError(409, "No active knowledge-base bundle is selected.")
    raise HttpError(
        409,
        f"Knowledge-base module '{module_name}' is not the active registered bundle.",
    )


def _load_module_kb(
    module_name: str, version: str | None = None
) -> KnowledgeBaseContract:
    loader = _kb_loader()
    resolved_version = (
        _resolve_active_version(module_name, version)
        if loader is _knowledge_base_resolver
        else version
    )
    try:
        if loader is _knowledge_base_resolver:
            loaded_kb = load_knowledge_base(module_name, version=resolved_version)
        else:
            try:
                loaded_kb = loader.load_knowledge_base(
                    module_name, version=resolved_version
                )
            except TypeError:
                loaded_kb = loader.load_knowledge_base(module_name)
        kb = cast(
            KnowledgeBaseContract,
            loaded_kb,
        )
    except KnowledgeBaseVersionNotFoundError as exc:
        raise HttpError(
            409,
            "Requested knowledge-base version is not provisioned locally for "
            f"module '{module_name}' and version '{resolved_version}'.",
        ) from exc
    except ValueError as exc:
        raise HttpError(404, f"Unknown knowledge-base module '{module_name}'.") from exc
    register_runtime_lookup_tracker(cast(Any, kb))
    return kb


def _resolve_report_template_module_location(
    module_name: str,
    version: str,
) -> ReportTemplateModuleLocation:
    version = version.strip()
    if not version:
        raise HttpError(
            400,
            "Report-template mutations require an explicit knowledge-base version.",
        )
    config = load_module_config(module_name, version=version)
    source_file = config.source_file
    if source_file is None:
        raise HttpError(
            409,
            f"Knowledge-base module '{module_name}' has no attributable source file.",
        )

    module_path = Path(source_file).resolve().parent
    modules_root = module_path.parent
    if config.name != module_name:
        raise HttpError(
            409,
            f"Resolved knowledge-base module '{config.name}' does not match '{module_name}'.",
        )
    try:
        expected_module_path = report_template_module_dir(
            module_name, modules_root=modules_root
        )
    except ValueError as exc:
        raise HttpError(409, str(exc)) from exc
    if expected_module_path != module_path:
        raise HttpError(
            409,
            f"Knowledge-base module '{module_name}' is not in its resolved module root.",
        )
    if modules_root.resolve() == package_data_root().resolve():
        raise HttpError(
            409,
            "Packaged report templates are immutable. Import an editable terminology "
            "bundle before saving or changing publication state.",
        )
    return ReportTemplateModuleLocation(
        module_name=module_name,
        version=version,
        modules_root=modules_root,
    )


def _kb_loader() -> Any:
    return _knowledge_base_resolver


def _clear_kb_caches() -> None:
    clear_findings_route_caches()
    clear_knowledge_base_resolver_caches()


def _resolve_payload_kb_identity(
    route_module_name: str,
    payload: PExamination,
) -> tuple[str, str]:
    payload_module_name = str(payload.knowledge_base_module or "").strip()
    payload_version = str(payload.knowledge_base_version or "").strip()

    if payload_module_name and payload_module_name != route_module_name:
        raise HttpError(
            409,
            "Payload knowledge-base module does not match route module: "
            f"'{payload_module_name}' != '{route_module_name}'.",
        )

    if not payload_version:
        raise HttpError(
            409,
            "Payload must include an explicit knowledge-base version.",
        )

    return payload_module_name or route_module_name, payload_version


def _api_error(status: int, code: str, message: str) -> NoReturn:
    raise StructuredApiError(status, code, message)


@runtime_checkable
class _RelatedManagerLike(Protocol):
    def all(self) -> Any: ...


def _as_str_list_from_relation(relation: object) -> list[str]:
    if relation is None:
        return []
    if isinstance(relation, _RelatedManagerLike):
        return [str(getattr(item, "pk", item)) for item in relation.all()]
    if isinstance(relation, list):
        return [str(item) for item in relation]
    return [str(relation)]


def _active_patient_findings_queryset() -> Any:
    from .findings_routes import _active_patient_findings_queryset as _active_queryset

    return _active_queryset(lambda: _orm_models())


def _build_p_examination_payload_from_host_ledger(
    patient_examination: object, *, route_module_name: str
) -> PExamination:
    return _build_payload_from_host_ledger(
        patient_examination,
        route_module_name=route_module_name,
        orm_models=lambda: _orm_models(),
        active_patient_findings_queryset=lambda: _active_patient_findings_queryset(),
    )


def _norm_name(value: Optional[str]) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


@lru_cache(maxsize=8)
def _kb_core_concepts(module_name: str) -> Dict[str, Any]:
    return _load_module_kb(module_name).export_core_concepts()


@lru_cache(maxsize=8)
def _kb_lookup(module_name: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    core = _kb_core_concepts(module_name)
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
    return {
        "examination": examination_by_name,
        "finding": finding_by_name,
        "classification": classification_by_name,
        "classification_choice": choice_by_name,
    }


def _request_user_if_authenticated(request: BaseRequest) -> Optional[Any]:
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        return user
    return None


def _serialize_choice(choice: Any) -> Dict[str, Any]:
    return {
        "id": choice.id,
        "name": choice.name,
        "description": choice.description,
        "subcategories": choice.subcategories,
        "numerical_descriptors": choice.numerical_descriptors,
    }


def _serialize_classification(
    classification: Any, *, required: bool = False
) -> Dict[str, Any]:
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
    classifications: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    location: List[Dict[str, Any]] = []
    morphology: List[Dict[str, Any]] = []
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
    allowed_classification_names: Optional[Set[str]] = None,
    required_classification_names: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    all_classifications = finding.finding_classifications.all().prefetch_related(
        "choices", "classification_types"
    )
    selected_classifications = []
    for classification in all_classifications:
        c_name = _norm_name(classification.name)
        if allowed_classification_names and c_name not in allowed_classification_names:
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
        # Keep compatibility with legacy frontend field access:
        "FindingClassifications": selected_classifications,
    }


def _serialize_patient_finding_classification(
    item: Any,
) -> Dict[str, Any]:
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


def _serialize_patient_finding(item: Any) -> Dict[str, Any]:
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
    examination: Any, *, module_name: str
) -> Optional[Set[str]]:
    lookup = _kb_lookup(module_name)
    exam_entry = lookup["examination"].get(_norm_name(examination.name))
    if not exam_entry:
        return None
    finding_names = exam_entry.get("findings", [])
    if not isinstance(finding_names, list):
        return None
    return {_norm_name(name) for name in finding_names}


def _resolve_kb_finding_classification_names(
    finding: Any, *, module_name: str
) -> Optional[Set[str]]:
    lookup = _kb_lookup(module_name)
    finding_entry = lookup["finding"].get(_norm_name(finding.name))
    if not finding_entry:
        return None
    classifications = finding_entry.get("classifications", [])
    if not isinstance(classifications, list):
        return None
    return {_norm_name(name) for name in classifications}


def _resolve_kb_classification_choice_names(
    classification: Any, *, module_name: str
) -> Optional[Set[str]]:
    lookup = _kb_lookup(module_name)
    classification_entry = lookup["classification"].get(_norm_name(classification.name))
    if not classification_entry:
        return None
    choices = classification_entry.get("classification_choices", [])
    if not isinstance(choices, list):
        return None
    return {_norm_name(name) for name in choices}


def _validate_finding_for_examination(
    finding: Any,
    patient_examination: Any,
    *,
    module_name: str,
) -> None:
    available_findings = patient_examination.examination_safe.get_available_findings()
    if finding not in available_findings:
        _api_error(
            400,
            "invalid-finding",
            f"Finding '{finding.name}' is not allowed for examination '{patient_examination.examination_safe.name}'.",
        )

    kb_allowed_names = _resolve_exam_kb_finding_names(
        patient_examination.examination_safe, module_name=module_name
    )
    if (
        kb_allowed_names is not None
        and _norm_name(finding.name) not in kb_allowed_names
    ):
        _api_error(
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
) -> None:
    if not finding.finding_classifications.filter(id=classification.id).exists():
        _api_error(
            400,
            "invalid-choice",
            f"Classification '{classification.name}' is not valid for finding '{finding.name}'.",
        )
    if not classification.choices.filter(id=choice.id).exists():
        _api_error(
            400,
            "invalid-choice",
            f"Choice '{choice.name}' is not valid for classification '{classification.name}'.",
        )

    kb_classifications = _resolve_kb_finding_classification_names(
        finding, module_name=module_name
    )
    if (
        kb_classifications is not None
        and _norm_name(classification.name) not in kb_classifications
    ):
        _api_error(
            400,
            "invalid-choice",
            f"Classification '{classification.name}' is not defined in dtypes for finding '{finding.name}'.",
        )

    kb_choices = _resolve_kb_classification_choice_names(
        classification, module_name=module_name
    )
    if kb_choices is not None and _norm_name(choice.name) not in kb_choices:
        _api_error(
            400,
            "invalid-choice",
            f"Choice '{choice.name}' is not defined in dtypes for classification '{classification.name}'.",
        )


def _replace_patient_finding_classifications(
    patient_finding: Any,
    entries: List[PatientFindingClassificationInput],
    *,
    module_name: str,
) -> None:
    patient_finding.classifications.all().delete()
    finding_classification_model = _orm_models()["FindingClassification"]
    finding_classification_choice_model = _orm_models()["FindingClassificationChoice"]
    patient_finding_classification_model = _orm_models()["PatientFindingClassification"]
    for entry in entries:
        classification = finding_classification_model.objects.filter(
            id=entry.classification
        ).first()
        if not classification:
            _api_error(
                400,
                "invalid-choice",
                f"Classification id '{entry.classification}' does not exist.",
            )
        choice = finding_classification_choice_model.objects.filter(
            id=entry.choice
        ).first()
        if not choice:
            _api_error(
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
        )
        patient_finding_classification_model.objects.create(
            finding=patient_finding,
            classification=classification,
            classification_choice=choice,
            is_active=True,
        )


register_report_template_routes(
    api,
    load_module_kb=lambda *args, **kwargs: _load_module_kb(*args, **kwargs),
    clear_kb_caches=lambda: _clear_kb_caches(),
    resolve_builder_module_location=lambda module_name, version: (
        _resolve_report_template_module_location(module_name, version)
    ),
    resolve_payload_kb_identity=lambda *args, **kwargs: _resolve_payload_kb_identity(
        *args, **kwargs
    ),
    orm_models=lambda: _orm_models(),
    build_p_examination_payload_from_host_ledger=lambda *args, **kwargs: (
        _build_p_examination_payload_from_host_ledger(*args, **kwargs)
    ),
    persist_patient_examination_dtypes_record=lambda *args, **kwargs: (
        _persist_patient_examination_dtypes_record(*args, **kwargs)
    ),
    authenticate_request_user=lambda request: _authenticate_request_user(request),
    report_template_access_allowed=lambda actor, capability: (
        _report_template_access_allowed(actor, capability)
    ),
)

register_knowledge_base_graph_routes(
    api,
    load_module_kb=lambda *args, **kwargs: _load_module_kb(*args, **kwargs),
)

register_findings_routes(
    api,
    load_module_kb=lambda *args, **kwargs: _load_module_kb(*args, **kwargs),
    orm_models=lambda: _orm_models(),
    api_error=lambda *args, **kwargs: _api_error(*args, **kwargs),
    authenticate_request_user=_authenticate_request_user,
    patient_examination_access_allowed=_patient_examination_access_allowed,
    patient_finding_access_allowed=_patient_finding_access_allowed,
    patient_findings_queryset_for_request=_patient_findings_queryset_for_request,
    build_p_examination_payload_from_host_ledger=lambda *args, **kwargs: (
        _build_p_examination_payload_from_host_ledger(*args, **kwargs)
    ),
    persist_patient_examination_dtypes_record=lambda *args, **kwargs: (
        _persist_patient_examination_dtypes_record(*args, **kwargs)
    ),
)

register_indications_routes(
    api,
    orm_models=lambda: _orm_models(),
    api_error=lambda *args, **kwargs: _api_error(*args, **kwargs),
)

register_examinations_routes(
    api,
    orm_models=lambda: _orm_models(),
    api_error=lambda *args, **kwargs: _api_error(*args, **kwargs),
)

register_terminology_routes(
    api,
    clear_kb_caches=lambda: _clear_kb_caches(),
    authenticate_request_user=(
        _authenticate_request_user if _host_integration_is_configured() else None
    ),
    terminology_write_access_allowed=(
        _terminology_write_access_allowed if _host_integration_is_configured() else None
    ),
)
