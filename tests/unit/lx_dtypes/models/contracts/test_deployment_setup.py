import json
from importlib.resources import files

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.deployment_setup import DeploymentSetup
from lx_dtypes.utils.deployment_setup import (
    parse_deployment_lock,
    parse_deployment_setup,
)


@pytest.mark.parametrize("name", ["minimal", "coloreg", "training", "green_endoscopy"])
def test_shipped_templates_use_frozen_schema(name: str) -> None:
    raw = files("lx_dtypes").joinpath("setup_templates", f"{name}.yml").read_text()
    setup = parse_deployment_setup(raw)
    assert setup.schema_version == "1.0"
    assert not any(p.activate for p in setup.study_packages)
    assert not setup.adopt_existing


def test_generated_editor_schema_matches_contract() -> None:
    schema = json.loads(
        files("lx_dtypes")
        .joinpath("setup_templates", "deployment_setup.schema.json")
        .read_text()
    )
    assert schema == DeploymentSetup.model_json_schema()


@pytest.mark.parametrize(
    "raw",
    [
        'schema_version: "1.0"\nschema_version: "1.0"',
        "site: &site {center_key: local, name: Local}\nother: *site",
        "!!python/object/apply:os.system [echo unsafe]",
        'schema_version: "1.0"\nsite: {center_key: local, name: Local}\nunknown: true',
        "schema_version: 1.0\nsite: {center_key: local, name: Local}",
        'schema_version: "1.0"\nsite: {center_key: local, name: "  "}',
        'schema_version: "1.0"\nsite: {center_key: local, name: Local}\nstudy_packages: [{module: a, version: "1", activate: true}, {module: b, version: "1", activate: true}]',
        'schema_version: "1.0"\nsite: {center_key: local, name: Local}\nreference_packages: [{module: a, version: "1"}, {module: a, version: "2"}]',
        'schema_version: "1.0"\nsite: {center_key: local, name: Local}\nreference_packages: [{module: a, version: "1", content_sha256: invalid}]',
    ],
)
def test_invalid_or_unsafe_setups_fail(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_deployment_setup(raw)


def test_lock_rejects_missing_selected_package() -> None:
    with pytest.raises(ValidationError, match="cover the manifest"):
        parse_deployment_lock("""schema_version: "1.0"
setup:
  schema_version: "1.0"
  site: {center_key: local, name: Local}
  reference_packages: [{module: a, version: "1"}]
packages: []
""")
