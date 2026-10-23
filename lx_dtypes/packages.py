"""Validated package authoring through the core KB and ledger contracts."""

import os
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import yaml

from lx_dtypes.language import DEFAULT_LANGUAGE, LanguageCode, validate_language
from lx_dtypes.models.base.app_base_model.pydantic.InterfaceMixIns import (
    ListFieldSerializationMixIn,
)
from lx_dtypes.models.contracts.validation import ValidationReport
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import KB_MODELS
from lx_dtypes.package_archive import (
    BinaryUpload,
    package_member_path,
    read_package_zip,
)
from lx_dtypes.serialization import parse_str_list
from lx_dtypes.terminology.terminology_loader import (
    get_terminology_service,
    load_module_kb,
)
from lx_dtypes.terminology.terminology_service import TerminologyService
from lx_dtypes.utils.kb_package_lint import check_kb_package
from lx_dtypes.utils.kb_yaml_lint import KbYamlLintIssue, discover_yaml_files
from lx_dtypes.utils.parser import camel_to_snake
from lx_dtypes.validation import assess_examination


@dataclass(frozen=True)
class PackageValidationResult:
    """Authoring diagnostics and optional ledger assessments in input order."""

    knowledge_base: KnowledgeBase | None
    files: tuple[Path, ...]
    issues: tuple[KbYamlLintIssue, ...]
    examinations: tuple[ValidationReport, ...] = ()

    @property
    def ok(self) -> bool:
        return (
            self.knowledge_base is not None
            and not self.issues
            and all(report.ok for report in self.examinations)
        )


class PackageValidationError(ValueError):
    def __init__(self, result: PackageValidationResult):
        self.result = result
        messages = [issue.format() for issue in result.issues]
        messages.extend(
            f"examinations[{index}]: {issue.code}: {issue.message}"
            for index, report in enumerate(result.examinations)
            for issue in report.issues
            if issue.level == "error"
        )
        super().__init__("\n".join(messages) or "Package could not be loaded.")


class PackageAuthoringWarning(UserWarning):
    """Advisory authoring diagnostic encountered while reading registered data."""


def validate_package(
    config_path: Path,
    *,
    examinations: Sequence[object] = (),
    template_name: str | None = None,
    language: LanguageCode = DEFAULT_LANGUAGE,
    input_dirs: Sequence[Path] | None = None,
) -> PackageValidationResult:
    """Load one exact manifest, check its graph, and assess optional ledger examples.

    Authoring warnings fail this quality gate. Ledger identity warnings retain
    the advisory API's legacy semantics. Invalid packages skip ledger assessment.
    Dependencies are resolved in the manifest's enclosing module tree.
    """
    validate_language(language)
    checked = check_kb_package(config_path, input_dirs=input_dirs)
    reports = (
        tuple(
            assess_examination(
                checked.knowledge_base,
                payload,
                template_name=template_name,
                language=language,
            )
            for payload in examinations
        )
        if checked.knowledge_base is not None and not checked.issues
        else ()
    )
    return PackageValidationResult(
        checked.knowledge_base, checked.files, checked.issues, reports
    )


def load_package(
    config_path: Path, *, input_dirs: Sequence[Path] | None = None
) -> KnowledgeBase:
    """Return a fully checked authoring package or raise with typed diagnostics."""
    result = validate_package(config_path, input_dirs=input_dirs)
    if not result.ok or result.knowledge_base is None:
        raise PackageValidationError(result)
    return result.knowledge_base


def load_registered_package(
    module_name: str,
    *,
    version: str | None = None,
    service: TerminologyService | None = None,
) -> KnowledgeBase:
    """Revalidate an exact registered source, retaining historical read support.

    Structural/graph errors fail. Authoring warnings are emitted as
    ``PackageAuthoringWarning``; new artifact authoring stays strictly gated.
    """
    selected_service = service if service is not None else get_terminology_service()
    kb = load_module_kb(module_name, version=version, service=selected_service)
    source = kb.config.source_file
    if source is None:
        raise ValueError("Registered knowledge base has no attributable source file.")
    result = validate_package(
        source,
        input_dirs=selected_service.source_paths(kb.config.name, kb.config.version),
    )
    if result.knowledge_base is None or any(
        issue.severity == "error" for issue in result.issues
    ):
        raise PackageValidationError(result)
    for issue in result.issues:
        warnings.warn(issue.format(), PackageAuthoringWarning, stacklevel=2)
    validated = result.knowledge_base
    if validated.config.knowledge_base_identity != kb.config.knowledge_base_identity:
        raise ValueError("Registered package identity changed during validation.")
    return validated


def build_package(
    destination: Path,
    files: Mapping[str, str | bytes],
    *,
    config_path: str = "config.yaml",
) -> Path:
    """Build a self-contained authored tree, validating before publishing it.

    The mapping includes every dependency. Paths are portable and relative;
    dependencies outside the staged tree cannot satisfy missing definitions.
    """
    selected = package_member_path(config_path)
    if selected.name != "config.yaml":
        raise ValueError("The package manifest must be named config.yaml.")
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".lx-package-", dir=destination.parent) as temporary:
        root = Path(temporary) / "package"
        root.mkdir()
        seen: set[str] = set()
        for name, content in files.items():
            relative = package_member_path(name)
            if relative.as_posix() in seen:
                raise ValueError("Duplicate package file path.")
            seen.add(relative.as_posix())
            target = root.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(
                content.encode("utf-8") if isinstance(content, str) else content
            )
        manifest = root.joinpath(*selected.parts)
        load_package(manifest, input_dirs=[root])
        _publish_folder(root, destination)
    return destination.joinpath(*selected.parts)


def read_package_archive(archive: Path | BinaryUpload) -> dict[str, bytes]:
    """Return validated portable files for publication by a host storage adapter."""
    if isinstance(archive, Path):
        with archive.open("rb") as source:
            files = read_package_zip(source)
    else:
        files = read_package_zip(archive)
    with TemporaryDirectory(prefix="lx-package-read-") as temporary:
        build_package(Path(temporary) / "package", files)
    return files


def import_package(archive: Path | BinaryUpload, destination: Path) -> Path:
    """Import a bounded ZIP into a new validated folder, without registration."""
    return build_package(destination, read_package_archive(archive))


def export_package_files(
    config_path: Path, *, input_dirs: Sequence[Path] | None = None
) -> dict[str, bytes]:
    """Export a portable, validated ZIP including the complete dependency closure.

    Existing internal layout and opaque resources are retained. Dependencies
    outside the package tree are placed under ``dependencies/<module>``.
    """
    load_package(config_path, input_dirs=input_dirs)
    config_path = config_path.resolve()
    configs: set[Path] = set()
    _, issues = discover_yaml_files(
        paths=[],
        config_paths=[config_path],
        resolved_configs=configs,
        input_dirs=input_dirs,
    )
    if issues:
        raise ValueError("\n".join(issue.format() for issue in issues))
    roots: dict[Path, Path] = {config_path.parent: Path()}
    for manifest in sorted(configs, key=lambda path: (len(path.parts), str(path))):
        if any(manifest.is_relative_to(root) for root in roots):
            continue
        config = KnowledgeBaseConfig.from_yaml_file(manifest)
        name = package_member_path(config.name)
        if len(name.parts) != 1:
            raise ValueError("Dependency names must be path-safe.")
        roots[manifest.parent] = Path("dependencies") / config.name
    files: dict[str, bytes] = {}
    for root, prefix in roots.items():
        for source in sorted(root.rglob("*")):
            if source.is_symlink():
                raise ValueError(f"Package symlinks are not supported: {source}")
            if not source.is_file():
                continue
            name = (prefix / source.relative_to(root)).as_posix()
            package_member_path(name)
            if name in files:
                raise ValueError(f"Conflicting package resource: {name}")
            files[name] = source.read_bytes()
    # Check portability and the archive limits through the same import boundary.
    return read_package_archive(BytesIO(_archive_bytes(files)))


def _archive_bytes(files: Mapping[str, bytes]) -> bytes:
    content = BytesIO()
    with ZipFile(content, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return content.getvalue()


def package_archive_bytes(
    config_path: Path, *, input_dirs: Sequence[Path] | None = None
) -> bytes:
    """Return validated ZIP bytes for a host-owned storage or HTTP adapter."""
    return _archive_bytes(export_package_files(config_path, input_dirs=input_dirs))


def export_package(
    config_path: Path, destination: Path, *, input_dirs: Sequence[Path] | None = None
) -> Path:
    """Export a validated portable ZIP, refusing an existing destination."""
    content = package_archive_bytes(config_path, input_dirs=input_dirs)
    destination = destination.absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(prefix=".lx-package-", dir=destination.parent) as target:
        target.write(content)
        target.flush()
        # Link publication is atomic and cannot replace a concurrent destination.
        os.link(target.name, destination)
    return destination


def _publish_folder(staged: Path, destination: Path) -> None:
    """Reserve a new directory before replacing it with the validated tree."""
    destination.mkdir()
    try:
        staged.rename(destination)
    except BaseException:
        destination.rmdir()
        raise


def _record_payload(record: KB_MODELS) -> dict[str, object]:
    payload: dict[str, object] = record.model_dump(
        mode="json", exclude_unset=True, exclude={"source_file", "kb_module_name"}
    )
    # Storage dumps flatten these fields; package YAML uses native lists.
    if isinstance(record, ListFieldSerializationMixIn):
        for field in record._get_all_list_fields():
            value = payload.get(field)
            if isinstance(value, str):
                payload[field] = parse_str_list(value)
    return {"model": camel_to_snake(type(record).__name__), **payload}


def create_package(
    destination: Path,
    *,
    name: str,
    version: str,
    records: Sequence[KB_MODELS] = (),
    depends_on: Sequence[str] = (),
) -> Path:
    """Create a checked package from core models, without replacing existing files.

    Dependencies must already exist in the enclosing module tree. Concepts and
    reporting records belong in separate packages linked through ``depends_on``.
    The returned manifest can be passed directly to ``load_package`` or ``ok``.
    """
    config = KnowledgeBaseConfig.model_validate(
        {
            "name": name,
            "version": version,
            "depends_on": list(depends_on),
            "data": {"files": ["records.yml"]},
        }
    )
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".lx-package-", dir=destination.parent) as staging:
        # Keep staging at the same architectural tier as sibling dependencies.
        root = Path(staging)
        manifest = root / "config.yaml"
        manifest.write_text(
            yaml.safe_dump(config.model_dump(mode="json", exclude_unset=True)),
            encoding="utf-8",
        )
        (root / "records.yml").write_text(
            yaml.safe_dump(
                [_record_payload(record) for record in records],
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        load_package(manifest)
        _publish_folder(root, destination)
    return destination / "config.yaml"


__all__ = [
    "PackageAuthoringWarning",
    "PackageValidationError",
    "PackageValidationResult",
    "build_package",
    "create_package",
    "export_package",
    "export_package_files",
    "import_package",
    "load_package",
    "load_registered_package",
    "package_archive_bytes",
    "read_package_archive",
    "validate_package",
]
