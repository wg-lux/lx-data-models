from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .json_types import JsonValue


def _normalize_role_names(role_names: list[str]) -> list[str]:
    normalized_roles: list[str] = []
    seen: set[str] = set()
    for role_name in role_names:
        normalized_role = role_name.strip()
        if normalized_role and normalized_role not in seen:
            normalized_roles.append(normalized_role)
            seen.add(normalized_role)
    return normalized_roles


def _normalize_group_paths(group_paths: list[str]) -> list[str]:
    normalized_groups: list[str] = []
    seen: set[str] = set()
    for group_path in group_paths:
        normalized_path = "/" + group_path.strip().strip("/")
        if normalized_path != "/" and normalized_path not in seen:
            normalized_groups.append(normalized_path)
            seen.add(normalized_path)
    return normalized_groups


class KeycloakRoleContainerPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    roles: list[str] = Field(default_factory=list)

    @field_validator("roles")
    @classmethod
    def normalize_roles(cls, value: list[str]) -> list[str]:
        return _normalize_role_names(value)


class KeycloakClaimsPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    preferred_username: str = ""
    sub: str = ""
    email: str = ""
    given_name: str = ""
    family_name: str = ""
    roles: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    realm_access: KeycloakRoleContainerPayload = Field(
        default_factory=KeycloakRoleContainerPayload
    )
    resource_access: dict[str, KeycloakRoleContainerPayload] = Field(
        default_factory=dict
    )

    @field_validator("preferred_username", "sub", "email", "given_name", "family_name")
    @classmethod
    def strip_claim_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("roles")
    @classmethod
    def normalize_roles(cls, value: list[str]) -> list[str]:
        return _normalize_role_names(value)

    @field_validator("groups")
    @classmethod
    def normalize_groups(cls, value: list[str]) -> list[str]:
        return _normalize_group_paths(value)

    @model_validator(mode="after")
    def require_subject_identifier(self) -> KeycloakClaimsPayload:
        if not self.preferred_username and not self.sub:
            raise ValueError("preferred_username or sub is required")
        return self

    @property
    def username(self) -> str:
        return self.preferred_username or self.sub

    @property
    def role_names(self) -> set[str]:
        """Return flat and realm roles that are safe for application authorization."""
        roles = set(self.roles)
        roles.update(self.realm_access.roles)
        return roles

    def role_names_for_resource(self, resource_name: str) -> set[str]:
        """Add roles for one explicitly trusted Keycloak resource/client."""
        normalized_resource_name = resource_name.strip()
        if not normalized_resource_name:
            raise ValueError("resource_name must not be blank")

        roles = self.role_names
        resource_entry = self.resource_access.get(normalized_resource_name)
        if resource_entry is not None:
            roles.update(resource_entry.roles)
        return roles


class AuthzRouteLookupPayload(BaseModel):
    """
    Normalized route/method lookup payload for authz policy checks.

    This deliberately allows empty strings so callers can preserve the
    existing secure-deny fallback behavior when route or method data is
    unavailable.
    """

    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    route_name: str = ""
    method: str = ""

    @field_validator("route_name")
    @classmethod
    def normalize_route_name(cls, value: str) -> str:
        return value.strip().split(":")[-1]

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.strip().upper()


class KeycloakTokenResponsePayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    access_token: str = Field(min_length=1)
    refresh_token: str = ""


def validate_keycloak_claims(
    payload: Mapping[str, JsonValue],
) -> KeycloakClaimsPayload:
    return KeycloakClaimsPayload.model_validate(dict(payload))


def validate_authz_route_lookup(
    payload: Mapping[str, JsonValue],
) -> AuthzRouteLookupPayload:
    return AuthzRouteLookupPayload.model_validate(dict(payload))


def validate_keycloak_token_response(
    payload: Mapping[str, JsonValue],
) -> KeycloakTokenResponsePayload:
    return KeycloakTokenResponsePayload.model_validate(dict(payload))


__all__ = [
    "AuthzRouteLookupPayload",
    "KeycloakClaimsPayload",
    "KeycloakRoleContainerPayload",
    "KeycloakTokenResponsePayload",
    "validate_authz_route_lookup",
    "validate_keycloak_claims",
    "validate_keycloak_token_response",
]
