from __future__ import annotations

import ast
import inspect
from types import SimpleNamespace as NS

import pytest
from conftest import ROOT, ApiError, TerminologyError, api_error


def route(h, method, path):
    return h.api.routes[method, path]


def catalog_identity(h, name=None, version=None, examination_id=None):
    return h.findings._resolve_catalog_kb_identity(
        name, version, lambda: h.models, examination_id, api_error
    )


def test_registration_uses_shared_provider_without_loader_injection(harness):
    h = harness
    assert (
        "load_module_kb"
        not in inspect.signature(h.findings.register_findings_routes).parameters
    )
    assert h.findings.load_module_kb is h.resolver.load_module_kb
    assert h.findings.active_kb_identity is h.examinations.active_kb_identity
    assert h.findings.active_kb_identity is h.resolver.active_kb_identity
    assert (
        len(h.api.routes) == 11
    )  # 9 findings operations plus 2 examination operations.
    h.resolver.load_module_kb.assert_not_called()
    h.resolver.active_kb_identity.assert_not_called()


def test_no_private_service_or_legacy_resolver_remains():
    source = (ROOT / "findings_routes.py").read_text()
    for forbidden in (
        "_LOAD_MODULE_KB",
        "_set_load_module_kb",
        "_require_load_module_kb",
        "TerminologyService",
        "active_terminology_selection",
        ".terminology_routes",
        "os.environ",
        "getenv(",
    ):
        assert forbidden not in source
    tree = ast.parse(source)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert any(
        isinstance(n.func, ast.Name) and n.func.id == "load_module_kb" for n in calls
    )


def test_catalog_discovery_reads_current_selection_each_time(harness):
    h = harness
    assert catalog_identity(h) == ("test_module", "v1")
    h.state.active = ("test_module", "v2")
    assert catalog_identity(h) == ("test_module", "v2")
    assert h.resolver.active_kb_identity.call_count == 2


def test_explicit_catalog_identity_never_reads_active(harness):
    h = harness
    h.state.active = None
    assert catalog_identity(h, " test_module ", " history ") == (
        "test_module",
        "history",
    )
    h.resolver.active_kb_identity.assert_not_called()


def test_exam_identity_never_reads_active(harness):
    h = harness
    h.state.active = None
    assert catalog_identity(h, examination_id=9) == ("test_module", "history")
    h.resolver.active_kb_identity.assert_not_called()


@pytest.mark.parametrize(
    "name,version",
    [("test_module", None), (None, "v1"), ("  ", "v1"), ("test_module", " ")],
)
def test_partial_requested_identity_is_409(harness, name, version):
    with pytest.raises(ApiError) as caught:
        catalog_identity(harness, name, version)
    assert (caught.value.status, caught.value.code) == (
        409,
        "knowledge-base-identity-required",
    )
    harness.resolver.active_kb_identity.assert_not_called()


def test_matching_explicit_and_exam_identity(harness):
    assert catalog_identity(harness, "test_module", "history", 9) == (
        "test_module",
        "history",
    )


def test_conflicting_requested_and_exam_identity(harness):
    with pytest.raises(ApiError) as caught:
        catalog_identity(harness, "test_module", "v1", 9)
    assert (caught.value.status, caught.value.code) == (
        409,
        "knowledge-base-identity-conflict",
    )
    harness.resolver.active_kb_identity.assert_not_called()


def test_missing_exam_is_404_not_active_fallback(harness):
    with pytest.raises(ApiError) as caught:
        catalog_identity(harness, examination_id=1234)
    assert caught.value.status == 404
    harness.resolver.active_kb_identity.assert_not_called()


@pytest.mark.parametrize("name,version", [("", ""), ("test_module", ""), ("", "v1")])
def test_pure_exam_resolver_rejects_incomplete_identity(harness, name, version):
    obj = NS(knowledge_base_module=name, knowledge_base_version=version)
    with pytest.raises(harness.findings.PatientExaminationKnowledgeBaseIdentityError):
        harness.findings._resolve_exam_kb_identity(obj)
    harness.resolver.active_kb_identity.assert_not_called()


def test_cache_keys_include_version(harness):
    h = harness
    v1 = h.findings._kb_lookup("test_module", version="v1")
    v2 = h.findings._kb_lookup("test_module", version="v2")
    assert "finding_v1" in v1["finding"]
    assert "finding_v2" in v2["finding"]
    assert h.findings._kb_lookup("test_module", version="v1") is v1
    assert h.resolver.load_module_kb.call_count == 2
    h.resolver.active_kb_identity.assert_not_called()


def test_exact_version_does_not_need_active_selection(harness):
    h = harness
    h.state.active = None
    core = h.findings._kb_core_concepts("test_module", "history")
    assert core["finding"][0]["name"] == "finding_history"
    h.resolver.load_module_kb.assert_called_once_with("test_module", version="history")


@pytest.mark.parametrize("version", ["", "   "])
def test_blank_version_is_rejected_not_replaced_by_active(harness, version):
    with pytest.raises(TerminologyError) as caught:
        harness.findings._kb_lookup("test_module", version=version)
    assert caught.value.status == 409
    harness.resolver.load_module_kb.assert_called_once_with("test_module", version="")


def test_module_only_helper_delegates_once_per_call(harness):
    h = harness
    assert "finding_v1" in h.findings._kb_lookup("test_module")["finding"]
    h.state.active = ("test_module", "v2")
    assert "finding_v2" in h.findings._kb_lookup("test_module")["finding"]
    assert h.resolver.load_module_kb.call_count == 2
    assert all(call.kwargs == {} for call in h.resolver.load_module_kb.call_args_list)


def test_unversioned_non_active_module_does_not_fallback(harness):
    with pytest.raises(TerminologyError):
        harness.findings._kb_lookup("another_module")
    harness.resolver.load_module_kb.assert_called_once_with("another_module")


def test_cache_clear_clears_both_exact_caches(harness):
    h = harness
    first = h.findings._kb_lookup("test_module", "v1")
    assert first["finding"]
    h.state.cores["test_module", "v1"] = {"finding": []}
    h.findings.clear_findings_route_caches()
    assert not h.findings._kb_lookup("test_module", "v1")["finding"]
    assert h.resolver.load_module_kb.call_count == 2


@pytest.mark.parametrize("status", [404, 409, 500])
def test_central_load_errors_keep_original_instance_and_status(harness, status):
    error = TerminologyError(status, "sentinel")
    harness.state.load_error = error
    with pytest.raises(TerminologyError) as caught:
        harness.findings._kb_lookup("test_module", "v1")
    assert caught.value is error


CATALOG_ROUTES = [
    ("/examinations/{examination_id}/findings/", "examination_id"),
    ("/findings/{finding_id}/classifications/", "finding_id"),
    ("/classifications/{classification_id}/choices/", "classification_id"),
]


@pytest.mark.parametrize("path,id_name", CATALOG_ROUTES)
def test_catalog_keeps_single_identity_if_active_changes_mid_response(
    harness, path, id_name
):
    h = harness

    def changing_selection():
        result = h.state.active
        h.state.active = ("test_module", "v2")
        return result

    h.resolver.active_kb_identity.side_effect = changing_selection
    result = route(h, "GET", path)(h.request, **{id_name: 1})
    assert result
    assert "v1" in str(result)
    assert "v2" not in str(result)
    h.resolver.active_kb_identity.assert_called_once_with()
    assert all(
        call.kwargs["version"] == "v1"
        for call in h.resolver.load_module_kb.call_args_list
    )


@pytest.mark.parametrize("path,id_name", CATALOG_ROUTES)
def test_catalog_central_errors_are_not_relabelled(harness, path, id_name):
    h = harness
    error = TerminologyError(500, "registry cannot be read")
    h.state.active_error = error
    with pytest.raises(TerminologyError) as caught:
        route(h, "GET", path)(h.request, **{id_name: 1})
    assert caught.value is error


def test_unexpected_runtime_error_not_disguised_as_missing_selection(harness):
    error = RuntimeError("a programming error")
    harness.state.active_error = error
    with pytest.raises(RuntimeError) as caught:
        route(harness, "GET", CATALOG_ROUTES[0][0])(harness.request, examination_id=1)
    assert caught.value is error


def test_core_endpoint_supports_explicit_version_and_does_not_mutate_export(harness):
    h = harness
    result = route(h, "GET", "/core-concepts/{module_name}")(
        h.request, "test_module", module_version="history"
    )
    assert result["knowledge_base_module"] == "test_module"
    assert result["knowledge_base_version"] == "history"
    assert result["finding"][0]["name"] == "finding_history"
    assert "knowledge_base_module" not in h.state.cores["test_module", "history"]
    h.resolver.load_module_kb.assert_called_once_with("test_module", version="history")


def test_core_endpoint_omitted_version_delegates_to_provider(harness):
    h = harness
    result = route(h, "GET", "/core-concepts/{module_name}")(h.request, "test_module")
    assert result["knowledge_base_version"] == "v1"
    h.resolver.load_module_kb.assert_called_once_with("test_module", version=None)


def test_legacy_shared_helper_signatures_still_support_examinations_and_indications(
    harness,
):
    h = harness
    assert h.findings._resolve_exam_kb_finding_names(
        h.exam, module_name="test_module", version="v1"
    ) == {"finding_v1"}
    assert h.findings._resolve_kb_finding_classification_names(
        h.found[0], module_name="test_module", version="v1"
    ) == {"classification_v1"}
    assert (
        "indication_v1"
        in h.findings._kb_lookup("test_module", version="v1")["indication"]
    )


def test_unknown_exam_has_no_allowed_findings(harness):
    assert (
        harness.findings._resolve_exam_kb_finding_names(
            NS(name="not_in_kb"), module_name="test_module", version="v1"
        )
        == set()
    )


def test_empty_allowlist_does_not_expose_all_classifications(harness):
    result = harness.findings._serialize_finding(
        harness.found[0], allowed_classification_names=set()
    )
    assert result["classifications"] == []
    assert result["FindingClassifications"] == []


WRITE_ROUTES = [
    (
        "POST",
        "/patient-findings/",
        "PatientFindingCreateRequest",
        {"patient_examination": 9, "finding": 3},
    ),
    (
        "PATCH",
        "/patient-findings/{patient_finding_id}/",
        "PatientFindingUpdateRequest",
        {"is_active": False},
    ),
    (
        "POST",
        "/patient-findings/{patient_finding_id}/classifications/",
        "PatientFindingClassificationsRequest",
        {"classifications": []},
    ),
]


def invoke_write(h, method, path, schema, data):
    kwargs = {"payload": getattr(h.findings, schema)(**data)}
    if "{patient_finding_id}" in path:
        kwargs["patient_finding_id"] = 4
    return route(h, method, path)(h.request, **kwargs)


@pytest.mark.parametrize("method,path,schema,data", WRITE_ROUTES)
def test_write_with_incomplete_exam_identity_is_409_before_mutation(
    harness, method, path, schema, data
):
    h = harness
    h.patient_exam.knowledge_base_version = ""
    with pytest.raises(ApiError) as caught:
        invoke_write(h, method, path, schema, data)
    assert (caught.value.status, caught.value.code) == (
        409,
        "knowledge-base-identity-required",
    )
    h.resolver.active_kb_identity.assert_not_called()
    h.patient_finding.save.assert_not_called()
    h.models["PatientFinding"].objects.create.assert_not_called()
    assert h.patient_finding.classifications.delete_calls == 0


@pytest.mark.parametrize("method,path,schema,data", WRITE_ROUTES)
def test_write_authorization_is_still_enforced(harness, method, path, schema, data):
    h = harness
    h.settings.allow_exam = h.settings.allow_finding = False
    with pytest.raises(ApiError) as caught:
        invoke_write(h, method, path, schema, data)
    assert caught.value.status == 404
    h.resolver.load_module_kb.assert_not_called()


@pytest.mark.parametrize("method,path,schema,data", WRITE_ROUTES)
def test_write_authentication_is_still_enforced(harness, method, path, schema, data):
    h = harness
    h.settings.actor = None
    with pytest.raises(ApiError) as caught:
        invoke_write(h, method, path, schema, data)
    assert caught.value.status == 401
    h.resolver.load_module_kb.assert_not_called()


def test_create_uses_exam_pinned_kb_not_active(harness):
    h = harness
    payload = h.findings.PatientFindingCreateRequest(patient_examination=9, finding=3)
    result = route(h, "POST", "/patient-findings/")(h.request, payload)
    assert result["id"] == 4
    h.resolver.load_module_kb.assert_called_once_with("test_module", version="history")
    h.resolver.active_kb_identity.assert_not_called()


def test_create_wrong_finding_for_pinned_version_is_rejected(harness):
    h = harness
    payload = h.findings.PatientFindingCreateRequest(patient_examination=9, finding=1)
    with pytest.raises(ApiError) as caught:
        route(h, "POST", "/patient-findings/")(h.request, payload)
    assert (caught.value.status, caught.value.code) == (400, "invalid-finding")
    h.models["PatientFinding"].objects.create.assert_not_called()


def test_exam_catalog_reads_active_only_once(harness):
    h = harness
    result = route(h, "GET", "/examinations/")(h.request)
    assert result[0]["findings"][0]["name"] == "finding_v1"
    h.resolver.active_kb_identity.assert_called_once_with()


def test_exam_detail_reads_active_only_once(harness):
    h = harness
    result = route(h, "GET", "/examinations/{examination_id}/")(h.request, 1)
    assert result["findings"][0]["name"] == "finding_v1"
    h.resolver.active_kb_identity.assert_called_once_with()


def test_exam_detail_missing_is_404_without_serializing_none(harness):
    h = harness
    with pytest.raises(ApiError) as caught:
        route(h, "GET", "/examinations/{examination_id}/")(h.request, 999)
    assert (caught.value.status, caught.value.code) == (404, "not-found")
    h.resolver.active_kb_identity.assert_not_called()


def test_exam_response_remains_pinned_through_all_serializer_calls(harness):
    h = harness
    h.resolver.active_kb_identity.side_effect = [
        ("test_module", "v1"),
        ("test_module", "v2"),
    ]
    result = route(h, "GET", "/examinations/")(h.request)
    assert result[0]["findings"][0]["classifications"][0]["name"] == "classification_v1"
    assert h.resolver.active_kb_identity.call_count == 1
    assert h.resolver.load_module_kb.call_args.kwargs["version"] == "v1"


def test_schema_mutable_defaults_are_independent(harness):
    schema = harness.findings.PatientFindingCreateRequest
    one, two = (
        schema(patient_examination=9, finding=3),
        schema(patient_examination=9, finding=3),
    )
    one.classifications.append(
        harness.findings.PatientFindingClassificationInput(classification=3, choice=3)
    )
    assert two.classifications == []


def test_clear_cache_callback_can_be_called_without_registration(harness):
    harness.findings.clear_findings_route_caches()
    assert harness.findings._kb_lookup_by_identity.cache_info().currsize == 0
