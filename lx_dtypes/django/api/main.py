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
    Literal,
    NoReturn,
    Optional,
    Protocol,
    Set,
    TypeVar,
    cast,
)

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone
from ninja.errors import HttpError
from pydantic import BaseModel, Field

from lx_dtypes.models.interface.DataLoader import DataLoader

from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


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
    Schema = BaseModel
    api = cast(_TypedApi, object())
else:
    from ninja import NinjaAPI, Schema

    api = cast(_TypedApi, NinjaAPI(urls_namespace="lx_dtypes_base_api"))


@lru_cache(maxsize=1)
def _orm_models() -> Dict[str, Any]:
    module_path = getattr(settings, "LX_DTYPES_HOST_MODELS_MODULE", None) or os.getenv(
        "LX_DTYPES_HOST_MODELS_MODULE"
    )
    if not module_path:
        raise RuntimeError(
            "LX_DTYPES_HOST_MODELS_MODULE must be configured to use lx_dtypes.django.api."
        )

    host_models = import_module(module_path)

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


class ReportTemplateValidationRequest(Schema):
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class PatientFindingClassificationInput(Schema):
    classification: int
    choice: int


class PatientFindingCreateRequest(Schema):
    patient_examination: int
    finding: int
    classifications: List[PatientFindingClassificationInput] = Field(
        default_factory=list
    )


class PatientFindingUpdateRequest(Schema):
    finding: Optional[int] = None
    is_active: Optional[bool] = None
    classifications: Optional[List[PatientFindingClassificationInput]] = None


class PatientFindingClassificationsRequest(Schema):
    classifications: List[PatientFindingClassificationInput] = Field(
        default_factory=list
    )
    replace: bool = True


@lru_cache(maxsize=1)
def _kb_loader() -> DataLoader:
    package_data_dir = Path(__file__).resolve().parents[2] / "data"
    legacy_cwd_data_dir = Path("./lx_dtypes/data/").resolve()
    input_dirs = [
        data_dir
        for data_dir in (package_data_dir, legacy_cwd_data_dir)
        if data_dir.exists()
    ]
    loader = DataLoader(input_dirs=input_dirs or [package_data_dir])
    loader.load_module_configs()
    return loader


def _load_module_kb(module_name: str) -> Any:
    loader = _kb_loader()
    try:
        return cast(Any, loader.load_knowledge_base(module_name))
    except ValueError as exc:
        raise HttpError(404, f"Unknown knowledge-base module '{module_name}'.") from exc


def _findings_module_name() -> str:
    return os.getenv("LX_DTYPES_FINDINGS_MODULE", "lx_knowledge_base")


def _norm_name(value: Optional[str]) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


@lru_cache(maxsize=8)
def _kb_core_concepts(module_name: str) -> Dict[str, Any]:
    return cast(Dict[str, Any], _load_module_kb(module_name).export_core_concepts())


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


def _active_patient_findings_queryset() -> QuerySet[Any]:
    patient_finding_model = _orm_models()["PatientFinding"]
    return cast(
        QuerySet[Any],
        patient_finding_model.objects.filter(is_active=True).select_related(
            "patient_examination", "finding"
        ),
    )


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


def _api_error(status: int, code: str, message: str) -> NoReturn:
    raise StructuredApiError(status, code, message)


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


@api.get("/hello")
def hello(request: BaseRequest) -> Literal["Hello world"]:
    """
    Return the fixed greeting used as the /hello endpoint response.

    Returns:
        The exact string "Hello world" returned to clients.
    """
    return "Hello world"


@api.get("/report-templates/{module_name}/{template_name}")
def report_template_by_name(
    request: BaseRequest, module_name: str, template_name: str
) -> Dict[str, Any]:
    """
    Return a resolved report template JSON payload by module/template name.
    """
    kb = _load_module_kb(module_name)
    try:
        return cast(Dict[str, Any], kb.export_report_template(template_name))
    except KeyError as exc:
        raise HttpError(
            404,
            f"Report template '{template_name}' not found in module '{module_name}'.",
        ) from exc


@api.get("/report-templates/by-examination/{module_name}/{examination_name}")
def report_templates_by_examination(
    request: BaseRequest, module_name: str, examination_name: str
) -> List[Dict[str, Any]]:
    """
    Return all resolved report templates for the given examination in one module.
    """
    kb = _load_module_kb(module_name)
    matches = [
        kb.export_report_template(template_name)
        for template_name, template in kb.report_template.items()
        if template.examination == examination_name
    ]
    return cast(List[Dict[str, Any]], matches)


@api.post("/report-templates/{module_name}/{template_name}/validate")
def validate_report_template_runtime(
    request: BaseRequest,
    module_name: str,
    template_name: str,
    payload: ReportTemplateValidationRequest,
) -> Dict[str, Any]:
    """
    Execute report-template validator logic against runtime finding payload data.
    """
    kb = _load_module_kb(module_name)
    try:
        return cast(
            Dict[str, Any],
            kb.evaluate_report_template_validators(
                template_name, reported_findings=payload.findings
            ),
        )
    except KeyError as exc:
        raise HttpError(
            404,
            f"Report template '{template_name}' not found in module '{module_name}'.",
        ) from exc


@api.get("/core-concepts/{module_name}")
def core_concepts_by_module(request: BaseRequest, module_name: str) -> Dict[str, Any]:
    """
    Return canonical core concept payloads for one KB module.
    """
    kb = _load_module_kb(module_name)
    return cast(Dict[str, Any], kb.export_core_concepts())


@api.get("/examinations/{examination_id}/findings/")
def findings_by_examination(
    request: BaseRequest, examination_id: int
) -> List[Dict[str, Any]]:
    module_name = _findings_module_name()
    examination_model = _orm_models()["Examination"]
    examination = examination_model.objects.filter(id=examination_id).first()
    if not examination:
        _api_error(404, "not-found", f"Examination '{examination_id}' not found.")

    assert examination is not None
    findings = list(examination.get_available_findings())
    kb_allowed_finding_names = _resolve_exam_kb_finding_names(
        examination, module_name=module_name
    )
    if kb_allowed_finding_names is not None:
        findings = [
            finding
            for finding in findings
            if _norm_name(finding.name) in kb_allowed_finding_names
        ]

    response = []
    for finding in findings:
        kb_allowed_classifications = _resolve_kb_finding_classification_names(
            finding, module_name=module_name
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
    request: BaseRequest, finding_id: int
) -> List[Dict[str, Any]]:
    module_name = _findings_module_name()
    finding_model = _orm_models()["Finding"]
    finding = finding_model.objects.filter(id=finding_id).first()
    if not finding:
        _api_error(404, "not-found", f"Finding '{finding_id}' not found.")
    assert finding is not None

    kb_allowed_classifications = _resolve_kb_finding_classification_names(
        finding, module_name=module_name
    )
    serialized = _serialize_finding(
        finding,
        allowed_classification_names=kb_allowed_classifications,
        required_classification_names=set(),
    )
    return cast(List[Dict[str, Any]], serialized["classifications"])


@api.get("/classifications/{classification_id}/choices/")
def choices_by_classification(
    request: BaseRequest, classification_id: int
) -> Dict[str, Any]:
    module_name = _findings_module_name()
    finding_classification_model = _orm_models()["FindingClassification"]
    classification = finding_classification_model.objects.filter(
        id=classification_id
    ).first()
    if not classification:
        _api_error(404, "not-found", f"Classification '{classification_id}' not found.")
    assert classification is not None

    kb_allowed_choices = _resolve_kb_classification_choice_names(
        classification, module_name=module_name
    )
    all_choices = list(classification.choices.all())
    if kb_allowed_choices is not None:
        all_choices = [
            choice
            for choice in all_choices
            if _norm_name(choice.name) in kb_allowed_choices
        ]
    return {"choices": [_serialize_choice(choice) for choice in all_choices]}


@api.get("/patient-findings/")
def list_patient_findings(
    request: BaseRequest, patient_examination: Optional[int] = None
) -> List[Dict[str, Any]]:
    queryset = _active_patient_findings_queryset()
    if patient_examination is not None:
        queryset = queryset.filter(patient_examination_id=patient_examination)
    return [_serialize_patient_finding(item) for item in queryset]


@api.post("/patient-findings/")
def create_patient_finding(
    request: BaseRequest, payload: PatientFindingCreateRequest
) -> Dict[str, Any]:
    module_name = _findings_module_name()
    patient_examination_model = _orm_models()["PatientExamination"]
    finding_model = _orm_models()["Finding"]
    patient_finding_model = _orm_models()["PatientFinding"]
    patient_examination = patient_examination_model.objects.filter(
        id=payload.patient_examination
    ).first()
    if not patient_examination:
        _api_error(
            404,
            "not-found",
            f"PatientExamination '{payload.patient_examination}' not found.",
        )
    finding = finding_model.objects.filter(id=payload.finding).first()
    if not finding:
        _api_error(404, "not-found", f"Finding '{payload.finding}' not found.")
    assert patient_examination is not None
    assert finding is not None

    _validate_finding_for_examination(
        finding=finding,
        patient_examination=patient_examination,
        module_name=module_name,
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
                )
            return _serialize_patient_finding(patient_finding)
    except IntegrityError as exc:
        if "unique_active_finding_per_examination" in str(exc):
            _api_error(
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
        _api_error(400, code, message)


@api.patch("/patient-findings/{patient_finding_id}/")
def patch_patient_finding(
    request: BaseRequest, patient_finding_id: int, payload: PatientFindingUpdateRequest
) -> Dict[str, Any]:
    module_name = _findings_module_name()
    patient_finding = (
        _active_patient_findings_queryset().filter(id=patient_finding_id).first()
    )
    if not patient_finding:
        _api_error(
            404, "not-found", f"Patient finding '{patient_finding_id}' not found."
        )
    assert patient_finding is not None

    with transaction.atomic():
        if payload.finding is not None:
            finding_model = _orm_models()["Finding"]
            finding = finding_model.objects.filter(id=payload.finding).first()
            if not finding:
                _api_error(404, "not-found", f"Finding '{payload.finding}' not found.")
            assert finding is not None
            _validate_finding_for_examination(
                finding=finding,
                patient_examination=patient_finding.patient_examination,
                module_name=module_name,
            )
            patient_finding.finding = finding

        if payload.is_active is not None:
            if payload.is_active:
                patient_finding.is_active = True
                patient_finding.deactivated_at = None
                patient_finding.deactivated_by = None
            else:
                patient_finding.is_active = False
                actor = _request_user_if_authenticated(request)
                patient_finding.deactivated_by = actor
                patient_finding.deactivated_at = (
                    timezone.now() if actor is not None else None
                )

        patient_finding.save()

        if payload.classifications is not None:
            _replace_patient_finding_classifications(
                patient_finding,
                payload.classifications,
                module_name=module_name,
            )

    return _serialize_patient_finding(patient_finding)


@api.delete("/patient-findings/{patient_finding_id}/")
def delete_patient_finding(
    request: BaseRequest, patient_finding_id: int
) -> Dict[str, Any]:
    patient_finding = (
        _active_patient_findings_queryset().filter(id=patient_finding_id).first()
    )
    if not patient_finding:
        _api_error(
            404, "not-found", f"Patient finding '{patient_finding_id}' not found."
        )
    assert patient_finding is not None

    actor = _request_user_if_authenticated(request)
    patient_finding.is_active = False
    patient_finding.deactivated_by = actor
    patient_finding.deactivated_at = timezone.now() if actor is not None else None
    patient_finding.save(
        update_fields=["is_active", "deactivated_at", "deactivated_by"]
    )
    return {"success": True, "id": patient_finding_id}


@api.post("/patient-findings/{patient_finding_id}/classifications/")
def set_patient_finding_classifications(
    request: BaseRequest,
    patient_finding_id: int,
    payload: PatientFindingClassificationsRequest,
) -> Dict[str, Any]:
    module_name = _findings_module_name()
    patient_finding = (
        _active_patient_findings_queryset().filter(id=patient_finding_id).first()
    )
    if not patient_finding:
        _api_error(
            404, "not-found", f"Patient finding '{patient_finding_id}' not found."
        )
    assert patient_finding is not None

    with transaction.atomic():
        finding_classification_model = _orm_models()["FindingClassification"]
        finding_classification_choice_model = _orm_models()[
            "FindingClassificationChoice"
        ]
        patient_finding_classification_model = _orm_models()[
            "PatientFindingClassification"
        ]
        if payload.replace:
            patient_finding.classifications.all().delete()
        for entry in payload.classifications:
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

    return _serialize_patient_finding(patient_finding)
