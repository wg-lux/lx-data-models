from __future__ import annotations

import pytest

import lx_dtypes
import lx_dtypes.models as lx_models
import lx_dtypes.models.interface as lx_interface
from lx_dtypes.models.contracts import (
    CoreConceptBase,
    KnowledgeBaseIdentity,
    PatientExaminationReportDraft,
)
from lx_dtypes.models.interface import load_knowledge_base
from lx_dtypes.models.interface.LookupTracker import KnowledgeBaseLookupTracker
from lx_dtypes.models.knowledge_base import KB_MODELS
from lx_dtypes.models.knowledge_base.report_template import ReportTemplate
from lx_dtypes.models.ledger import L_MODELS
from lx_dtypes.models.main import MODELS


def test_lx_dtypes_lazy_exports_cover_all_dispatch_branches() -> None:
    assert lx_dtypes.ReportTemplate is ReportTemplate
    assert lx_dtypes.CoreConceptBase is CoreConceptBase
    assert lx_dtypes.KnowledgeBaseIdentity is KnowledgeBaseIdentity
    assert lx_dtypes.PatientExaminationReportDraft is PatientExaminationReportDraft
    assert lx_dtypes.load_knowledge_base is load_knowledge_base

    with pytest.raises(AttributeError):
        getattr(lx_dtypes, "does_not_exist")


def test_models_lazy_exports_cover_knowledge_base_ledger_and_main() -> None:
    assert lx_models.KB_MODELS is KB_MODELS
    assert lx_models.L_MODELS is L_MODELS
    assert lx_models.MODELS is MODELS

    with pytest.raises(AttributeError):
        getattr(lx_models, "does_not_exist")


def test_interface_lazy_exports_cover_lookup_tracker_and_resolver() -> None:
    assert lx_interface.KnowledgeBaseLookupTracker is KnowledgeBaseLookupTracker
    assert lx_interface.load_knowledge_base is load_knowledge_base

    with pytest.raises(AttributeError):
        getattr(lx_interface, "does_not_exist")
