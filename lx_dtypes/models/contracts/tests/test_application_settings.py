from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.application_settings import (
    ApplicationSettingsBackupSourcePayload,
    ApplicationSettingsBackupStatusPayload,
    ApplicationSettingsDeploymentProfilePayload,
)


def test_backup_status_accepts_consistent_source_summary() -> None:
    status = ApplicationSettingsBackupStatusPayload(
        ready=False,
        missing_paths=("/protected",),
        required_path_count=2,
        available_path_count=1,
        source_roots=(
            ApplicationSettingsBackupSourcePayload(
                label="protected_root",
                path="/protected",
                exists=False,
                file_count=0,
            ),
            ApplicationSettingsBackupSourcePayload(
                label="storage",
                path="/storage",
                exists=True,
                file_count=3,
            ),
        ),
    )

    assert status.available_path_count == 1


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"required_path_count": 1}, "required_path_count"),
        ({"available_path_count": 2}, "available_path_count"),
        ({"missing_paths": ()}, "missing_paths"),
        ({"ready": True}, "ready"),
    ],
)
def test_backup_status_rejects_inconsistent_source_summary(
    overrides: dict[str, object],
    message: str,
) -> None:
    payload: dict[str, object] = {
        "ready": False,
        "missing_paths": ("/protected",),
        "required_path_count": 2,
        "available_path_count": 1,
        "source_roots": (
            ApplicationSettingsBackupSourcePayload(
                label="protected_root",
                path="/protected",
                exists=False,
                file_count=0,
            ),
            ApplicationSettingsBackupSourcePayload(
                label="storage",
                path="/storage",
                exists=True,
                file_count=3,
            ),
        ),
    }
    payload.update(overrides)

    with pytest.raises(ValidationError, match=message):
        ApplicationSettingsBackupStatusPayload.model_validate(payload)


def test_backup_source_rejects_files_for_missing_path() -> None:
    with pytest.raises(ValidationError, match="missing backup source"):
        ApplicationSettingsBackupSourcePayload(
            label="storage",
            path="/storage",
            exists=False,
            file_count=1,
        )


def test_deployment_profile_accepts_consistent_derived_flags() -> None:
    profile = ApplicationSettingsDeploymentProfilePayload(
        deployment_role="central_hub",
        hub_mode=True,
        enable_hub_transfers=True,
        transfer_api_enabled=True,
        transfer_require_secure_transport=True,
        transfer_require_mtls=True,
    )

    assert profile.transfer_api_enabled is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"hub_mode": False},
        {"transfer_api_enabled": False},
    ],
)
def test_deployment_profile_rejects_inconsistent_derived_flags(
    overrides: dict[str, object],
) -> None:
    payload: dict[str, object] = {
        "deployment_role": "central_hub",
        "hub_mode": True,
        "enable_hub_transfers": True,
        "transfer_api_enabled": True,
        "transfer_require_secure_transport": True,
        "transfer_require_mtls": True,
    }
    payload.update(overrides)

    with pytest.raises(ValidationError):
        ApplicationSettingsDeploymentProfilePayload.model_validate(payload)


def test_deployment_profile_rejects_secret_transport_metadata() -> None:
    with pytest.raises(ValidationError, match="transfer_mtls_meta_value"):
        ApplicationSettingsDeploymentProfilePayload.model_validate(
            {
                "deployment_role": "standalone",
                "hub_mode": False,
                "enable_hub_transfers": False,
                "transfer_api_enabled": False,
                "transfer_require_secure_transport": True,
                "transfer_require_mtls": False,
                "transfer_mtls_meta_value": "secret",
            }
        )
