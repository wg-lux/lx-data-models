from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import ValidationError, validate_keycloak_claims


def test_keycloak_claims_default_roles_exclude_client_resources() -> None:
    claims = validate_keycloak_claims(
        {
            "preferred_username": "alice",
            "email": "alice@example.test",
            "given_name": "Alice",
            "family_name": "Example",
            "roles": ["flat-role"],
            "realm_access": {"roles": ["realm-role"]},
            "resource_access": {
                "account": {"roles": ["manage-account"]},
                "endoregdb-api": {"roles": ["api-read", "api-write"]},
            },
        }
    )

    assert claims.username == "alice"
    assert claims.role_names == {
        "flat-role",
        "realm-role",
    }


def test_keycloak_claims_include_only_explicit_resource_roles() -> None:
    claims = validate_keycloak_claims(
        {
            "preferred_username": "alice",
            "roles": [" flat-role ", "flat-role", ""],
            "realm_access": {"roles": [" realm-role ", "realm-role"]},
            "resource_access": {
                "account": {"roles": ["manage-account"]},
                "endoregdb-api": {"roles": [" api-read ", "api-write"]},
            },
        }
    )

    assert claims.role_names_for_resource("endoregdb-api") == {
        "flat-role",
        "realm-role",
        "api-read",
        "api-write",
    }
    assert "manage-account" not in claims.role_names_for_resource("endoregdb-api")


def test_keycloak_claims_reject_blank_explicit_resource_name() -> None:
    claims = validate_keycloak_claims({"sub": "subject-id"})

    with pytest.raises(ValueError, match="resource_name"):
        claims.role_names_for_resource("  ")


def test_keycloak_claims_fall_back_to_subject() -> None:
    claims = validate_keycloak_claims({"sub": "subject-id"})

    assert claims.username == "subject-id"
    assert claims.role_names == set()


def test_keycloak_claims_reject_blank_subject_identifier() -> None:
    with pytest.raises(ValidationError):
        validate_keycloak_claims({"preferred_username": "  ", "sub": ""})


def test_keycloak_claims_reject_non_string_roles() -> None:
    with pytest.raises(ValidationError):
        validate_keycloak_claims({"roles": [1]})
