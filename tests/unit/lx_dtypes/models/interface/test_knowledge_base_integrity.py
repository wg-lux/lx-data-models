"""Tripwires for the integrity of shipped knowledge bases as the resolver serves them.

``test_knowledge_base_resolver.py`` proves the resolver mechanics with synthetic
bundles. This suite asserts that the *shipped* catalog keeps its guarantees when it
is consumed through :mod:`lx_dtypes.models.interface.KnowledgeBaseResolver`:

* every catalog release resolves through the production provider path with an
  exact identity and passes the runtime fail-closed template-validator gate;
* the unversioned development path serves each module's catalog default;
* retained (non-default) releases are immutable and isolated by layout;
* tampered installed bytes or rewritten identities are refused, never served;
* a published template with a dangling validator reference is refused at runtime.

A failure here means terminology served to hosts may differ from what a recorded
``module@version`` promised. Never update a pin or catalog digest to make a test
pass. Run ``uv run python scripts/kb_catalog.py status`` for a per-release
diagnosis, and publish intended changes with
``uv run python scripts/kb_catalog.py new-version <module> <next-version>``.
See docs/guides/terminology-releases.md.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable, Iterator
from importlib.resources.abc import Traversable
from pathlib import Path

import pytest

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    PackagedKnowledgeBase,
    get_packaged_knowledge_base,
    knowledge_base_content_sha256,
    list_packaged_knowledge_bases,
)
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseRegistryError,
    KnowledgeBaseVersionConflictError,
    clear_knowledge_base_resolver_caches,
    get_knowledge_base_identity,
    load_knowledge_base,
    load_module_config,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
PINS_FILE = REPO_ROOT / "tests/fixtures/lx_dtypes/retained_release_bundles.json"
STATUS_HINT = (
    "Run `uv run python scripts/kb_catalog.py status` for a diagnosis and fix; "
    "see docs/guides/terminology-releases.md."
)


def _load_retained_pins() -> dict[str, str]:
    """Bundle digests of retained releases, appended by ``kb_catalog new-version``.

    A retained bundle holds the module and the dependency modules it was
    published with; the pin covers all of them, not only the catalog digest.
    """

    payload = json.loads(PINS_FILE.read_text(encoding="utf-8"))
    return dict(payload["retained_releases"])


RETAINED_RELEASE_PINS = _load_retained_pins()

PACKAGED_RELEASES = list_packaged_knowledge_bases()
DEFAULT_RELEASES = tuple(item for item in PACKAGED_RELEASES if item.default)
RETAINED_RELEASES = tuple(item for item in PACKAGED_RELEASES if not item.default)

# Small, dependency-free retained bundles used as tamper and validator subjects.
TAMPER_SUBJECT = ("polyp_size_category", "1.0.0")
VALIDATOR_SUBJECT = ("star_upper_gi", "0.1.1.post1")


def _identity_id(item: PackagedKnowledgeBase) -> str:
    return f"{item.module_name}@{item.version}"


def _write_provider_registry(
    registry_path: Path,
    descriptors: tuple[PackagedKnowledgeBase, ...],
) -> None:
    modules: dict[str, dict[str, object]] = {}
    for descriptor in descriptors:
        modules.setdefault(descriptor.module_name, {})[descriptor.version] = {
            "sources": [
                {
                    "kind": "provider",
                    "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                    "content_sha256": descriptor.content_sha256,
                }
            ]
        }
    registry_path.write_text(json.dumps({"modules": modules}), encoding="utf-8")


def _resource_path(descriptor: PackagedKnowledgeBase) -> Path:
    return Path(str(descriptor.resource_directory())).resolve()


@pytest.fixture(autouse=True)
def _isolated_resolver(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("LX_DTYPES_KB_REGISTRY", raising=False)
    clear_knowledge_base_resolver_caches()
    yield
    clear_knowledge_base_resolver_caches()


# --------------------------------------------------------------------------- #
# Shipped catalog through the production resolver path
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("descriptor", PACKAGED_RELEASES, ids=_identity_id)
def test_every_packaged_release_resolves_through_the_provider_registry(
    descriptor: PackagedKnowledgeBase,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    _write_provider_registry(registry_path, (descriptor,))
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    # load_knowledge_base also enforces the runtime fail-closed validator gate.
    knowledge_base = load_knowledge_base(
        descriptor.module_name, version=descriptor.version
    )

    assert (knowledge_base.config.name, knowledge_base.config.version) == (
        descriptor.module_name,
        descriptor.version,
    )
    assert get_knowledge_base_identity(
        descriptor.module_name, version=descriptor.version
    ) == (descriptor.module_name, descriptor.version)
    source_file = knowledge_base.config.source_file
    assert source_file is not None
    # The served root module must come from this release's own resource
    # directory, never from a sibling version reachable via the search root.
    assert source_file.resolve().parent == _resource_path(descriptor), (
        f"{_identity_id(descriptor)} was served from {source_file}, not from its "
        f"catalog resource_root {descriptor.resource_root}. Another directory "
        "declares the same module; check for a stray copy. " + STATUS_HINT
    )


def test_full_catalog_registry_serves_each_version_distinctly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    _write_provider_registry(registry_path, PACKAGED_RELEASES)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    served = {
        (item.module_name, item.version): load_module_config(
            item.module_name, version=item.version
        )
        for item in PACKAGED_RELEASES
    }

    for (module_name, version), config in served.items():
        assert (config.name, config.version) == (module_name, version)
    source_files = [config.source_file for config in served.values()]
    assert len(set(source_files)) == len(source_files), (
        "two catalog identities resolved to the same config.yaml"
    )


@pytest.mark.parametrize("descriptor", DEFAULT_RELEASES, ids=_identity_id)
def test_unversioned_development_load_serves_the_catalog_default(
    descriptor: PackagedKnowledgeBase,
) -> None:
    config = load_module_config(descriptor.module_name)

    assert config.version == descriptor.version, (
        f"Loading {descriptor.module_name} without a version served "
        f"{config.version}, but the catalog default is {descriptor.version}. "
        "config.yaml `version` must only change through `uv run python "
        "scripts/kb_catalog.py new-version`. " + STATUS_HINT
    )
    assert config.source_file is not None
    assert config.source_file.resolve().parent == _resource_path(descriptor), (
        f"{descriptor.module_name} was served from {config.source_file}, not from "
        f"its catalog resource_root {descriptor.resource_root}. " + STATUS_HINT
    )


# --------------------------------------------------------------------------- #
# Retained release immutability and layout
# --------------------------------------------------------------------------- #


def test_every_retained_release_is_pinned() -> None:
    retained = {_identity_id(item) for item in RETAINED_RELEASES}

    unpinned = sorted(retained - RETAINED_RELEASE_PINS.keys())
    removed = sorted(RETAINED_RELEASE_PINS.keys() - retained)

    assert not unpinned, (
        f"Retained releases without a bundle pin in {PINS_FILE.name}: {unpinned}. "
        "Retain releases with `uv run python scripts/kb_catalog.py new-version "
        "<module> <next-version>`, which records the pin. " + STATUS_HINT
    )
    assert not removed, (
        f"Pinned releases were removed from the catalog or made default again: "
        f"{removed}. Hosts may have pinned them; restore their catalog entries "
        "(`git restore lx_dtypes/data/catalog.json`). " + STATUS_HINT
    )


@pytest.mark.parametrize(
    "descriptor",
    [item for item in RETAINED_RELEASES if _identity_id(item) in RETAINED_RELEASE_PINS],
    ids=_identity_id,
)
def test_retained_release_bundle_is_immutable(
    descriptor: PackagedKnowledgeBase,
) -> None:
    # Recomputes the module digest from installed bytes and checks its identity;
    # its error message explains how to restore or re-version the release.
    descriptor.verified_resource_directory()

    bundle_root = descriptor.installed_data_root()
    bundle_path = bundle_root.relative_to(REPO_ROOT / "lx_dtypes").as_posix()
    actual = knowledge_base_content_sha256(bundle_root)
    assert actual == RETAINED_RELEASE_PINS[_identity_id(descriptor)], (
        f"Retained release {_identity_id(descriptor)} changed: the YAML in "
        f"lx_dtypes/{bundle_path} (the module or the dependency modules "
        "snapshotted with it) no longer matches its pin. Retained releases are "
        f"frozen. Restore them with `git restore lx_dtypes/{bundle_path}`, then "
        f"make the correction in the default release of {descriptor.module_name} "
        "and publish it with `uv run python scripts/kb_catalog.py new-version "
        f"{descriptor.module_name} <next-version>`. Never edit the pin. " + STATUS_HINT
    )


@pytest.mark.parametrize("descriptor", RETAINED_RELEASES, ids=_identity_id)
def test_retained_release_lives_in_its_own_versioned_directory(
    descriptor: PackagedKnowledgeBase,
) -> None:
    expected_suffix = (
        "versions",
        descriptor.module_name,
        descriptor.version,
        descriptor.module_name,
    )

    parts = tuple(Path(descriptor.resource_root).parts)

    assert parts[-4:] == expected_suffix, (
        f"Retained release {_identity_id(descriptor)} must live in "
        f"versions/{descriptor.module_name}/{descriptor.version}/"
        f"{descriptor.module_name} so it never shares files with another version; "
        f"found {descriptor.resource_root}. `kb_catalog.py new-version` creates "
        "this layout. " + STATUS_HINT
    )
    assert descriptor.installed_data_root().resolve() == (
        _resource_path(descriptor).parent
    )


# --------------------------------------------------------------------------- #
# Tampered installs are refused, not served
# --------------------------------------------------------------------------- #


def _append_comment(root: Path) -> None:
    with (root / "data.yml").open("a", encoding="utf-8") as handle:
        handle.write("# silently edited after release\n")


def _add_yaml_file(root: Path) -> None:
    (root / "injected.yml").write_text("[]\n", encoding="utf-8")


def _delete_yaml_file(root: Path) -> None:
    (root / "numeric_rules.yml").unlink()


def _rename_yaml_file(root: Path) -> None:
    (root / "numeric_rules.yml").rename(root / "numeric_rules.yaml")


def _rewrite_config_version(root: Path) -> None:
    config_path = root / "config.yaml"
    text = config_path.read_text(encoding="utf-8")
    assert "version: 1.0.0\n" in text
    config_path.write_text(
        text.replace("version: 1.0.0\n", "version: 9.9.9\n"), encoding="utf-8"
    )


@pytest.fixture
def installed_tamper_subject(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Path:
    """Install a private copy of a retained release and route the provider to it.

    Returns the copied module directory, which tests may tamper with before
    resolving. The registry pins the genuine catalog digest.
    """

    module_name, version = TAMPER_SUBJECT
    descriptor = get_packaged_knowledge_base(module_name, version)
    install_root = tmp_path / "site" / "versions" / module_name / version
    shutil.copytree(descriptor.installed_data_root(), install_root)
    module_dir = install_root / module_name

    original_resource_directory = PackagedKnowledgeBase.resource_directory

    def _resource_directory(self: PackagedKnowledgeBase) -> Traversable:
        if (self.module_name, self.version) == TAMPER_SUBJECT:
            return module_dir
        return original_resource_directory(self)

    monkeypatch.setattr(
        PackagedKnowledgeBase, "resource_directory", _resource_directory
    )
    registry_path = tmp_path / "kb_registry.json"
    _write_provider_registry(registry_path, (descriptor,))
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    return module_dir


def test_untampered_install_copy_is_served(installed_tamper_subject: Path) -> None:
    module_name, version = TAMPER_SUBJECT

    knowledge_base = load_knowledge_base(module_name, version=version)

    assert knowledge_base.config.source_file is not None
    assert knowledge_base.config.source_file.parent == installed_tamper_subject


@pytest.mark.parametrize(
    "tamper",
    [_append_comment, _add_yaml_file, _delete_yaml_file, _rename_yaml_file],
    ids=["edited-bytes", "added-yaml", "deleted-yaml", "renamed-yaml"],
)
def test_tampered_install_bytes_are_refused(
    installed_tamper_subject: Path,
    tamper: Callable[[Path], None],
) -> None:
    module_name, version = TAMPER_SUBJECT
    tamper(installed_tamper_subject)

    with pytest.raises(
        KnowledgeBaseVersionConflictError, match="digest mismatch"
    ) as excinfo:
        load_knowledge_base(module_name, version=version)
    with pytest.raises(KnowledgeBaseVersionConflictError, match="digest mismatch"):
        load_module_config(module_name, version=version)
    _assert_retained_release_guidance(str(excinfo.value))


def test_rewritten_install_identity_is_refused(
    installed_tamper_subject: Path,
) -> None:
    module_name, version = TAMPER_SUBJECT
    _rewrite_config_version(installed_tamper_subject)

    with pytest.raises(
        KnowledgeBaseRegistryError, match="identity conflicts"
    ) as excinfo:
        load_knowledge_base(module_name, version=version)
    message = str(excinfo.value)
    assert "does not create a new release" in message
    _assert_retained_release_guidance(message)


def _assert_retained_release_guidance(message: str) -> None:
    """Integrity errors must tell both audiences what to do next."""

    module_name, version = TAMPER_SUBJECT
    resource_root = get_packaged_knowledge_base(module_name, version).resource_root
    assert "published releases are immutable" in message
    assert "reinstall the package" in message
    assert f"git restore lx_dtypes/{resource_root}" in message
    assert f"scripts/kb_catalog.py new-version {module_name}" in message
    assert "docs/guides/terminology-releases.md" in message


def test_default_release_guidance_offers_a_new_version() -> None:
    descriptor = get_packaged_knowledge_base("coloreg")
    assert descriptor.default

    message = descriptor.remediation()

    assert f"git restore lx_dtypes/{descriptor.resource_root}" in message
    assert "scripts/kb_catalog.py new-version coloreg <next-version>" in message
    assert "retains the committed bytes of coloreg@" in message


def test_registry_digest_conflict_explains_host_and_maintainer_fixes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    descriptor = get_packaged_knowledge_base(*TAMPER_SUBJECT)
    registry_path = tmp_path / "kb_registry.json"
    _write_provider_registry(
        registry_path,
        (descriptor.model_copy(update={"content_sha256": "0" * 64}),),
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    with pytest.raises(KnowledgeBaseVersionConflictError) as excinfo:
        load_module_config(descriptor.module_name, version=descriptor.version)

    message = str(excinfo.value)
    assert "Host operators" in message
    assert "Never edit the registry digest" in message
    assert "lx-dtypes maintainers" in message
    assert "new-version polyp_size_category" in message


# --------------------------------------------------------------------------- #
# Runtime fail-closed template validator gate
# --------------------------------------------------------------------------- #


@pytest.fixture
def validator_subject_copy(tmp_path: Path) -> Path:
    module_name, version = VALIDATOR_SUBJECT
    descriptor = get_packaged_knowledge_base(module_name, version)
    data_root = tmp_path / "versions" / module_name / version
    shutil.copytree(descriptor.installed_data_root(), data_root)
    return data_root


def test_published_template_with_dangling_validator_is_refused_at_runtime(
    validator_subject_copy: Path,
) -> None:
    module_name, version = VALIDATOR_SUBJECT
    template_path = validator_subject_copy / module_name / "report_template.yaml"
    text = template_path.read_text(encoding="utf-8")
    assert text.count("findings_validators: []") == 1
    template_path.write_text(
        text.replace(
            "findings_validators: []",
            "findings_validators: [integrity_probe_missing_validator]",
        ),
        encoding="utf-8",
    )

    # Authoring and lint paths still load the draft to report diagnostics ...
    loader = DataLoader(input_dirs=[validator_subject_copy])
    loader.load_module_configs()
    draft = loader.load_knowledge_base(module_name)
    assert draft.unresolved_template_validator_references() == (
        (
            "star_upper_gi_main",
            "findings_validator",
            "integrity_probe_missing_validator",
        ),
    )

    # ... but the runtime resolver must never serve it.
    with pytest.raises(ValueError, match="integrity_probe_missing_validator"):
        load_knowledge_base(
            module_name,
            version=version,
            input_dirs=[validator_subject_copy],
        )


def test_unmodified_validator_subject_copy_is_served(
    validator_subject_copy: Path,
) -> None:
    module_name, version = VALIDATOR_SUBJECT

    knowledge_base = load_knowledge_base(
        module_name,
        version=version,
        input_dirs=[validator_subject_copy],
    )

    assert knowledge_base.config.version == version
