"""Isolated route harness: real Python/Pydantic; explicit framework/KB/ORM doubles.

No installed Django, Ninja or lx-dtypes application is exercised. Tests import
our delivered route modules under a temporary package and restore sys.modules.
"""

from __future__ import annotations

import importlib.util
import sys
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[1]


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code = status, code
        super().__init__(message)


def api_error(status, code, message):
    raise ApiError(status, code, message)


class TerminologyError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


class Query:
    def __init__(self, items=()):
        self.items = list(items)
        self.delete_calls = 0

    def __iter__(self):
        return iter(self.items)

    def all(self):
        return self

    def filter(self, **kwargs):
        return Query(
            item
            for item in self.items
            if all(getattr(item, key, None) == val for key, val in kwargs.items())
        )

    def first(self):
        return self.items[0] if self.items else None

    def exists(self):
        return bool(self.items)

    def select_related(self, *args):
        return self

    def prefetch_related(self, *args):
        return self

    def order_by(self, name):
        return Query(sorted(self.items, key=lambda obj: getattr(obj, name)))

    def delete(self):
        self.delete_calls += 1
        self.items.clear()

    @classmethod
    def __class_getitem__(cls, item):
        return cls


class FakeApi:
    def __init__(self):
        self.routes = {}

    def _register(self, method, path):
        def decorator(func):
            key = method, path
            assert key not in self.routes
            self.routes[key] = func
            return func

        return decorator

    def get(self, path):
        return self._register("GET", path)

    def post(self, path):
        return self._register("POST", path)

    def patch(self, path):
        return self._register("PATCH", path)

    def delete(self, path):
        return self._register("DELETE", path)


class PassthroughDTO(BaseModel):
    model_config = ConfigDict(extra="allow")


@pytest.fixture
def harness(monkeypatch):
    def module(name, **attrs):
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            path = ".".join(parts[:i])
            if path not in sys.modules:
                obj = ModuleType(path)
                obj.__path__ = []
                monkeypatch.setitem(sys.modules, path, obj)
            if i > 1:
                monkeypatch.setattr(
                    sys.modules[".".join(parts[: i - 1])],
                    parts[i - 1],
                    sys.modules[path],
                    raising=False,
                )
        result = sys.modules[name]
        for key, value in attrs.items():
            monkeypatch.setattr(result, key, value, raising=False)
        return result

    module(
        "django.core.exceptions",
        ValidationError=type("ValidationError", (Exception,), {}),
    )
    module(
        "django.db",
        IntegrityError=type("IntegrityError", (Exception,), {}),
        transaction=NS(atomic=nullcontext),
    )
    module("django.db.models", QuerySet=Query)
    module("django.utils.timezone", now=lambda: datetime.now(UTC))
    module("ninja", Schema=BaseModel)
    module(
        "lx_dtypes.models.ledger.p_examination.Pydantic", PExamination=PassthroughDTO
    )
    module(
        "lx_dtypes.models.contracts.terminology_catalog",
        ExaminationCatalogDTO=PassthroughDTO,
    )

    state = NS(
        active=("test_module", "v1"), load_error=None, active_error=None, cores={}
    )
    for version in ("v1", "v2", "history"):
        state.cores["test_module", version] = {
            "examination": [
                {
                    "name": "exam",
                    "findings": [f"finding_{version}"],
                    "indications": [f"indication_{version}"],
                }
            ],
            "finding": [
                {
                    "name": f"finding_{version}",
                    "classifications": [f"classification_{version}"],
                }
            ],
            "classification": [
                {
                    "name": f"classification_{version}",
                    "classification_choices": [f"choice_{version}"],
                }
            ],
            "classification_choice": [{"name": f"choice_{version}"}],
            "indication": [{"name": f"indication_{version}"}],
        }

    def active():
        if state.active_error is not None:
            raise state.active_error
        if state.active is None:
            raise TerminologyError(409, "No active knowledge-base bundle is selected.")
        return state.active

    def load(name, *, version=None):
        if state.load_error is not None:
            raise state.load_error
        name = name.strip()
        if not name:
            raise TerminologyError(409, "Module must not be empty.")
        if version is None:
            selected_name, selected_version = active()
            if name != selected_name:
                raise TerminologyError(
                    409, "An explicit version is required for a non-active module."
                )
            version = selected_version
        else:
            version = version.strip()
            if not version:
                raise TerminologyError(409, "Version must not be empty.")
        key = name, version
        if key not in state.cores:
            raise TerminologyError(404, "Unknown bundle.")
        return NS(
            config=NS(name=name, version=version),
            export_core_concepts=lambda: state.cores[key],
        )

    resolver = module(
        "lx_dtypes.terminology.terminology_loader",
        active_kb_identity=Mock(side_effect=active),
        load_module_kb=Mock(side_effect=load),
    )
    module("route_harness", __path__=[str(ROOT)])
    module("route_harness.request_types", BaseRequest=NS)

    def load_route(name):
        qualified = f"route_harness.{name}"
        spec = importlib.util.spec_from_file_location(qualified, ROOT / f"{name}.py")
        assert spec is not None and spec.loader is not None
        obj = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, qualified, obj)
        spec.loader.exec_module(obj)
        return obj

    findings = load_route("findings_routes")
    examinations = load_route("examinations_routes")

    choices, classifications, found = [], [], []
    for i, version in enumerate(("v1", "v2", "history"), 1):
        choice = NS(
            id=i,
            name=f"choice_{version}",
            description="",
            subcategories=[],
            numerical_descriptors={},
        )
        classification = NS(
            id=i,
            name=f"classification_{version}",
            description="",
            choices=Query([choice]),
            classification_types=Query([]),
        )
        finding = NS(
            id=i,
            name=f"finding_{version}",
            description="",
            finding_classifications=Query([classification]),
        )
        choices.append(choice)
        classifications.append(classification)
        found.append(finding)
    exam = NS(
        id=1,
        name="exam",
        get_available_findings=lambda: found,
        examination_types=Query([]),
    )
    patient_exam = NS(
        id=9,
        examination_id=exam.id,
        examination=exam,
        examination_safe=exam,
        knowledge_base_module="test_module",
        knowledge_base_version="history",
    )
    patient_finding = NS(
        id=4,
        patient_examination=patient_exam,
        patient_examination_id=9,
        finding=found[2],
        finding_id=3,
        classifications=Query([]),
        is_active=True,
        created_at=None,
        updated_at=None,
        save=Mock(),
    )
    models = {
        "Examination": NS(objects=Query([exam])),
        "PatientExamination": NS(objects=Query([patient_exam])),
        "Finding": NS(objects=Query(found)),
        "FindingClassification": NS(objects=Query(classifications)),
        "FindingClassificationChoice": NS(objects=Query(choices)),
        "PatientFinding": NS(objects=NS(create=Mock(return_value=patient_finding))),
        "PatientFindingClassification": NS(objects=NS(create=Mock())),
    }
    settings = NS(actor=NS(id=1), allow_exam=True, allow_finding=True)
    api = FakeApi()
    kwargs = {
        "orm_models": lambda: models,
        "api_error": api_error,
        "authenticate_request_user": lambda request: settings.actor,
        "patient_examination_access_allowed": lambda request, obj: settings.allow_exam,
        "patient_finding_access_allowed": lambda request, obj: settings.allow_finding,
        "patient_findings_queryset_for_request": lambda request: Query(
            [patient_finding]
        ),
    }
    findings.register_findings_routes(api, **kwargs)
    examinations.register_examinations_routes(
        api, orm_models=lambda: models, api_error=api_error
    )
    return NS(
        findings=findings,
        examinations=examinations,
        api=api,
        kwargs=kwargs,
        models=models,
        state=state,
        resolver=resolver,
        request=NS(),
        exam=exam,
        patient_exam=patient_exam,
        patient_finding=patient_finding,
        settings=settings,
        found=found,
    )
