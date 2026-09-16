"""Isolated transport doubles; LXDM models, loaders, schemas and files are real.

Run in a dedicated pytest process. Do not load this into the application's full
Django test run: HTTP/ORM adapters are deliberately replaced here.
"""

from __future__ import annotations

import sys
import types
from contextlib import nullcontext
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import BaseModel


def module(name: str, **values: object) -> types.ModuleType:
    value = types.ModuleType(name)
    value.__path__ = []
    value.__dict__.update(values)
    sys.modules[name] = value
    return value


settings = SimpleNamespace(TERMINOLOGY_ROOT=None)
module("django")
module("django.conf", settings=settings)
module("django.core")
module(
    "django.core.exceptions",
    ImproperlyConfigured=type("ImproperlyConfigured", (Exception,), {}),
    ValidationError=type("ValidationError", (Exception,), {}),
)
module("django.http", HttpRequest=type("HttpRequest", (), {}))


class QuerySet:
    @classmethod
    def __class_getitem__(cls, item):
        return cls


module(
    "django.db",
    IntegrityError=type("IntegrityError", (Exception,), {}),
    transaction=SimpleNamespace(atomic=nullcontext),
)
module("django.db.models", QuerySet=QuerySet)
module("django.utils")
module("django.utils.timezone", now=lambda: datetime.now(UTC))


class HttpError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


class FakeAPI:
    def __init__(self, **kwargs):
        self.routes = {}

    def route(self, path, **kwargs):
        def bind(fn):
            self.routes[path] = fn
            return fn

        return bind

    get = post = patch = delete = exception_handler = route

    def create_response(self, request, data, *, status):
        return status, data


module(
    "ninja",
    Schema=BaseModel,
    NinjaAPI=FakeAPI,
    Router=FakeAPI,
    File=lambda *args, **kwargs: None,
)
module("ninja.errors", HttpError=HttpError)
module("ninja.files", UploadedFile=type("UploadedFile", (), {}))
# This request DTO is imported by the findings module but not exercised here.
module("lx_dtypes.models.ledger.p_examination.Pydantic", PExamination=BaseModel)

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)
from lx_dtypes.terminology import terminology_loader as central
from lx_dtypes.terminology.terminology_service import TerminologyService


@pytest.fixture(scope="session")
def seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("real_lxdm_seed") / "terminology"
    service = TerminologyService(root / "registry.json")
    service.provision()
    return root


@pytest.fixture
def storage(seed, tmp_path, monkeypatch):
    import shutil

    root = tmp_path / "runtime"
    shutil.copytree(seed, root)
    registry = root / "registry.json"
    payload = registry.read_text()
    registry.write_text(payload.replace(str(seed), str(root)))
    monkeypatch.setattr(settings, "TERMINOLOGY_ROOT", root)
    central.get_terminology_service.cache_clear()
    clear_knowledge_base_resolver_caches()
    yield root
    central.get_terminology_service.cache_clear()
    clear_knowledge_base_resolver_caches()


@pytest.fixture
def api():
    return FakeAPI()
