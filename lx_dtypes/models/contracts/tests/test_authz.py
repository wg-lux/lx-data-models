from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import ValidationError, validate_keycloak_claims


def test_keycloak_claims_merge_flat_realm_and_resource_roles() -> None:
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
        "manage-account",
        "api-read",
        "api-write",
    }


def test_keycloak_claims_fall_back_to_subject() -> None:
    claims = validate_keycloak_claims({"sub": "subject-id"})

    assert claims.username == "subject-id"
    assert claims.role_names == set()


def test_keycloak_claims_reject_non_string_roles() -> None:
    with pytest.raises(ValidationError):
        validate_keycloak_claims({"roles": [1]})
