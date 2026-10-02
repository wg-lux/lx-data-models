"""Resolve and fingerprint explicit deployment selections without persistent writes."""

from __future__ import annotations

from dataclasses import dataclass

from lx_dtypes.knowledge_bases import knowledge_base_content_sha256
from lx_dtypes.models.contracts.deployment_setup import (
    DeploymentLock,
    DeploymentPackage,
    DeploymentPackageLock,
    DeploymentSetup,
    DeploymentSource,
    source_closure_digest,
)
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.terminology.terminology_service import TerminologyService
from lx_dtypes.utils.study_setup_yaml import parse_setup_yaml


@dataclass(frozen=True)
class ResolvedDeployment:
    lock: DeploymentLock
    knowledge_bases: dict[str, KnowledgeBase]


def parse_deployment_setup(raw: str) -> DeploymentSetup:
    return DeploymentSetup.model_validate(parse_setup_yaml(raw))


def parse_deployment_lock(raw: str) -> DeploymentLock:
    return DeploymentLock.model_validate(parse_setup_yaml(raw))


def _source(config: KnowledgeBaseConfig) -> DeploymentSource:
    if config.source_file is None:
        raise ValueError("deployment sources require a registered filesystem manifest")
    return DeploymentSource(
        module=config.name,
        version=config.version,
        content_sha256=knowledge_base_content_sha256(config.source_file.parent),
    )


def resolve_deployment(
    setup: DeploymentSetup, service: TerminologyService
) -> ResolvedDeployment:
    """Pin source bytes, including transitive modules; reject concurrent edits.

    Config/data writes, registry hydration and implicit remote downloads do not
    belong in validate or plan. Register remote artifacts locally first.
    """
    setup = DeploymentSetup.model_validate_json(setup.model_dump_json())
    packages: dict[str, DeploymentPackage] = {
        p.module: p for p in [*setup.reference_packages, *setup.study_packages]
    }
    locked: list[DeploymentPackageLock] = []
    bases: dict[str, KnowledgeBase] = {}
    closure: dict[str, DeploymentSource] = {}
    for package in sorted(packages.values(), key=lambda p: p.module):
        paths = service.source_paths(
            package.module, package.version, allow_remote=False
        )
        loader = DataLoader(input_dirs=paths)
        configs = loader.resolved_module_configs(package.module)
        before = sorted(
            (_source(config) for config in configs), key=lambda source: source.module
        )
        kb = loader.load_knowledge_base(package.module)
        if (kb.config.name, kb.config.version) != (package.module, package.version):
            raise ValueError(f"resolved identity mismatch for {package.module}")
        # Re-resolve too: config edits can change dependency edges.
        after_loader = DataLoader(input_dirs=paths)
        after = sorted(
            (
                _source(config)
                for config in after_loader.resolved_module_configs(package.module)
            ),
            key=lambda source: source.module,
        )
        if before != after:
            raise ValueError(f"package sources changed while loading {package.module}")
        for source in before:
            if source.module in closure and closure[source.module] != source:
                raise ValueError(f"incompatible shared dependency {source.module}")
            closure[source.module] = source
        digest = source_closure_digest(package.module, package.version, before)
        if package.content_sha256 is not None and package.content_sha256 != digest:
            raise ValueError(f"content digest mismatch for {package.module}")
        locked.append(
            DeploymentPackageLock(
                module=package.module,
                version=package.version,
                content_sha256=digest,
                sources=before,
            )
        )
        bases[package.module] = kb
    return ResolvedDeployment(
        lock=DeploymentLock(setup=setup, packages=locked), knowledge_bases=bases
    )
