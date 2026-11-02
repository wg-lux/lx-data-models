"""Discover knowledge-base ``config.yaml`` files and assemble one validated module graph.

When to use it
--------------
Use :class:`DataLoader` where you deliberately work on knowledge-base *sources*:
authoring tools, package linting and validation, registry bootstrap, and tests.
It reads whatever ``config.yaml`` files exist under ``input_dirs``; it does not
know which version a host has selected.

Runtime and API code should not create ad-hoc loaders. Resolve one explicit
``knowledge_base_module``/``knowledge_base_version`` identity through
:func:`lx_dtypes.models.interface.load_knowledge_base` (the registry-aware
resolver), which uses a ``DataLoader`` internally on exactly that identity's
inputs. See ``docs/guides/knowledge-base-contract-migration.md``.

How loading works
-----------------
1. **Discover**: :meth:`DataLoader.load_module_configs` finds every
   ``config.yaml`` below ``input_dirs`` (missing directories are skipped) and
   parses each into a :class:`KnowledgeBaseConfig`. Paths in ``data.dirs`` and
   ``data.files`` are resolved against the ``config.yaml`` directory, so a
   module directory can be moved as a whole.
2. **Resolve**: :meth:`DataLoader.resolved_module_configs` selects the root
   module and the transitive closure of its ``depends_on`` and ``modules``
   references, dependencies first. Cycles raise :class:`ValueError`.
3. **Assemble**: :meth:`DataLoader.load_knowledge_base` builds a
   :class:`KnowledgeBase` per resolved config, imports them into the root
   module's knowledge base in that order, and records the exact configs used.
   Pydantic validation of every record happens here.

Example (packaged data, no dependencies)::

    >>> from lx_dtypes.models.interface.data_roots import package_data_root
    >>> loader = DataLoader(input_dirs=[package_data_root()])
    >>> kb = loader.load_knowledge_base("polyp_size_category")
    >>> (kb.config.name, kb.config.version)
    ('polyp_size_category', '2.0.0')
    >>> [config.name for config in loader.resolved_module_configs("polyp_size_category")]
    ['polyp_size_category']

Which config wins when a name appears more than once
----------------------------------------------------
Retained releases and bundles can contain the same module name several times.
A reference is resolved in this order, and anything still ambiguous fails:

1. A config next to the referencing module (``<dir>/<name>/config.yaml`` or a
   sibling directory), so a bundle uses its own copy.
2. The canonical location ``<input_dir>/terminology|report_templates/<name>``,
   then ``<input_dir>/<name>``, then a grouped ``terminology/config.yaml``.
3. Candidates from the same release tree as the referencing module.
4. The only remaining candidate. Several left raise
   :class:`AmbiguousModuleConfigError`, listing every candidate path; narrow
   ``input_dirs`` to the intended release instead of relying on order.

A name with no config raises :class:`ModuleConfigNotFoundError`.

Cost and repeated runs
----------------------
Loading parses and validates every YAML record of the closure, which takes
seconds per module. A loader caches discovered configs; call
:meth:`DataLoader.load_module_configs` again after files change, or create a
new loader. Do not run full loads on every process start: the deployment
bootstrap (``lx-dtypes-kb-registry bootstrap``) persists validation receipts
and only reloads identities whose inputs or lx-dtypes version changed. See
"Startup bootstrap and migration" in ``docs/guides/knowledge-base-authoring.md``.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.models.interface.data_roots import module_search_root
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.utils.dataloader import (
    _default_dataloader_dirs_factory,
    resolve_kb_module_load_order,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


class ModuleConfigNotFoundError(ValueError):
    """Raised when an explicitly referenced module has no configuration."""


class AmbiguousModuleConfigError(ValueError):
    """Raised when a module name resolves to more than one config candidate."""


class DataLoader(AppBaseModel):
    """Loads knowledge-base modules from ``config.yaml`` sources; see the module docs.

    Attributes:
        input_dirs: Directories searched recursively for ``config.yaml``.
            Defaults to the configured data roots (packaged data unless the
            host overrides them). Pass the exact release directories you mean
            to load; broad roots containing retained versions are more likely
            to be ambiguous.
        module_configs: The last discovered config per module name, filled by
            :meth:`load_module_configs`.
        module_config_candidates: Every discovered config per module name,
            used to resolve duplicates.
    """

    input_dirs: list[Path] = Field(default_factory=_default_dataloader_dirs_factory)
    module_configs: dict[str, "KnowledgeBaseConfig"] = Field(default_factory=dict)
    module_config_candidates: dict[str, list["KnowledgeBaseConfig"]] = Field(
        default_factory=dict
    )

    def load_knowledge_base(self, module_name: str) -> "KnowledgeBase":
        """Build the validated knowledge base of ``module_name`` and its whole closure.

        Discovers configs on first use, resolves the root module and its
        dependencies (dependencies first), validates every module's records
        and imports them into the root module's knowledge base. Local concept
        definitions in reporting packages emit one warning per module.

        Args:
            module_name: Semantic module name from ``config.yaml`` (``name``),
                not necessarily the directory name.

        Returns:
            The root module's knowledge base, including all imported modules.

        Raises:
            ModuleConfigNotFoundError: The module or a referenced one has no config.
            AmbiguousModuleConfigError: A name resolves to several configs.
            ValueError: A dependency cycle or invalid record was found.
        """
        from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

        configs = self.resolved_module_configs(module_name)
        modules = {
            config.name: KnowledgeBase.create_from_config(config, warn_concepts=False)
            for config in configs
        }
        reporting_names = {
            name for name, module in modules.items() if module.is_reporting_package
        }
        # Resolved config.modules includes the transitive dependency closure.
        for config in configs:
            modules[config.name].warn_local_concept_definitions(
                reporting_context=bool(reporting_names.intersection(config.modules))
            )
        kb = modules[configs[0].name]
        for config in configs[1:]:
            kb.import_knowledge_base(modules[config.name])
        kb._resolved_module_configs = {
            config.name: config.model_copy(deep=True) for config in configs
        }
        return kb

    def resolved_module_configs(
        self, module_name: str
    ) -> tuple["KnowledgeBaseConfig", ...]:
        """Return the exact configurations consumed by loading, root first.

        Use it to inspect which files a load would read (for example to lint
        exactly those YAML files) without validating records. The root's
        ``modules`` list is already in dependency order.

        Keep this shared with load_knowledge_base: dependency traversal alone
        is insufficient when a bundle scopes a module also available globally.
        """
        if not self.module_configs:
            self.load_module_configs()
        root = self._get_initialized_config(module_name)
        return (
            root,
            *(
                self._get_initialized_config(
                    name, context_config=root, relation="module"
                )
                for name in root.modules
            ),
        )

    def fetch_config_yamls(self) -> list[Path]:
        """Return every ``config.yaml`` below the existing ``input_dirs``.

        Missing or non-directory inputs are skipped silently here; a module
        that is then absent fails later with :class:`ModuleConfigNotFoundError`.
        """
        config_files: list[Path] = []
        for input_dir in self.input_dirs:
            if not input_dir.exists() or not input_dir.is_dir():
                continue

            config_files.extend(input_dir.rglob("config.yaml"))

        return config_files

    def load_module_configs(self) -> None:
        """(Re)discover and parse every ``config.yaml``, replacing cached configs.

        Each file becomes a :class:`KnowledgeBaseConfig` whose ``data`` paths
        are resolved against the file's directory. Files are read in sorted
        path order, so results do not depend on filesystem order. All
        candidates per name are kept for resolution; ``module_configs`` holds
        the last one only as a legacy convenience. Call this again after
        changing files on disk.
        """

        config_files = sorted(
            {config_file.resolve() for config_file in self.fetch_config_yamls()}
        )
        self.module_configs = {}
        self.module_config_candidates = {}
        for config_file in config_files:
            kb_config = KnowledgeBaseConfig.from_yaml_file(config_file)
            self.module_config_candidates.setdefault(kb_config.name, []).append(
                kb_config
            )
            self.module_configs[kb_config.name] = kb_config

    def get_initialized_config(self, module_name: str) -> "KnowledgeBaseConfig":
        """Return a copy of the module's config with ``modules`` in dependency order.

        ``modules`` then lists the full transitive closure, dependencies
        before dependents, preserving declared order where possible.
        """

        return self._get_initialized_config(module_name)

    def _get_initialized_config(
        self,
        module_name: str,
        *,
        context_config: "KnowledgeBaseConfig | None" = None,
        relation: Literal["root", "module", "dependency"] = "root",
    ) -> "KnowledgeBaseConfig":
        """Return a config initialized with references resolved in context."""

        if not self.module_configs:
            self.load_module_configs()

        stored_config = self.resolve_module_config(
            module_name,
            context_config=context_config,
            relation=relation,
        )

        kb_config = stored_config.model_copy(deep=True)

        # Preserve declared order but ensure dependencies are placed ahead of dependents.
        requested_modules = list(
            dict.fromkeys([*kb_config.depends_on, *kb_config.modules])
        )
        if not requested_modules:
            return kb_config

        module_configs, preferred_order = self._collect_module_closure(
            requested_modules,
            context_config=kb_config,
        )
        load_order = resolve_kb_module_load_order(
            module_configs,
            preferred_order,
        )
        kb_config.modules = load_order
        return kb_config

    def _configs_for_name(self, module_name: str) -> list["KnowledgeBaseConfig"]:
        """All discovered candidates; falls back to ``module_configs`` set directly by callers."""
        candidates = self.module_config_candidates.get(module_name)
        if candidates:
            return candidates

        legacy_config = self.module_configs.get(module_name)
        return [legacy_config] if legacy_config is not None else []

    def resolve_module_config(
        self,
        module_name: str,
        *,
        context_config: "KnowledgeBaseConfig | None" = None,
        relation: Literal["root", "module", "dependency"] = "root",
    ) -> "KnowledgeBaseConfig":
        """Select one config for ``module_name`` using the source-scope rules.

        Args:
            module_name: The referenced semantic module name.
            context_config: The referencing module's config; its location makes
                a bundle prefer its own copy of a module.
            relation: ``root`` for the requested module, ``module`` for a
                child listed in ``modules``, ``dependency`` for ``depends_on``.
                It changes which neighbouring directory is tried first.

        The order is documented in the module docstring under "Which config
        wins when a name appears more than once".
        """
        candidates = self._configs_for_name(module_name)
        if not candidates:
            if relation == "dependency":
                raise ModuleConfigNotFoundError(
                    f"Module '{module_name}' is referenced but no configuration was loaded for it."
                )
            raise ModuleConfigNotFoundError(
                f"Module '{module_name}' is not loaded. Call 'load_module_configs' first."
            )

        preferred_paths = self._preferred_config_paths(
            module_name,
            context_config=context_config,
            relation=relation,
        )
        for preferred_path in preferred_paths:
            matched = [
                candidate
                for candidate in candidates
                if candidate.source_file is not None
                and candidate.source_file.resolve() == preferred_path
            ]
            if len(matched) == 1:
                return matched[0]

        # Semantic module names need not match directory names. Prefer the
        # caller's release tree over unrelated retained copies of that module.
        if context_config is not None and context_config.source_file is not None:
            scope = module_search_root(context_config.source_file)
            scoped = [
                candidate
                for candidate in candidates
                if candidate.source_file is not None
                and module_search_root(candidate.source_file) == scope
            ]
            if scoped:
                candidates = scoped

        if len(candidates) == 1:
            return candidates[0]

        candidate_paths = ", ".join(
            str(candidate.source_file or "<unknown>") for candidate in candidates
        )
        raise AmbiguousModuleConfigError(
            f"Module '{module_name}' is ambiguous; found multiple config.yaml "
            f"candidates: {candidate_paths}."
        )

    def _preferred_config_paths(
        self,
        module_name: str,
        *,
        context_config: "KnowledgeBaseConfig | None",
        relation: Literal["root", "module", "dependency"],
    ) -> list[Path]:
        """Exact ``config.yaml`` paths to try, most specific first.

        With a referencing module: its own child/sibling directory (child
        first for ``modules``, sibling first for ``depends_on``), then the
        canonical category locations, then ``<input_dir>/<name>``, then grouped
        ``terminology/config.yaml`` manifests. For a root request: a unique
        ``<input_dir>/<name>`` match, else a unique canonical category match.
        An empty list defers to release-tree scoping.
        """
        if context_config is not None and context_config.source_file is not None:
            context_dir = context_config.source_file.parent
            if relation == "module":
                contextual_paths = [
                    (context_dir / module_name / "config.yaml").resolve(),
                    (context_dir.parent / module_name / "config.yaml").resolve(),
                ]
            else:
                contextual_paths = [
                    (context_dir.parent / module_name / "config.yaml").resolve(),
                    (context_dir / module_name / "config.yaml").resolve(),
                ]
            canonical_paths = [
                (input_dir / category / module_name / "config.yaml").resolve()
                for input_dir in self.input_dirs
                for category in ("terminology", "report_templates")
            ]
            # Some grouped packages declare their semantic module name in the
            # terminology/config.yaml manifest (for example DGVS_Terminology).
            # Matching still requires this exact path among that name's configs.
            grouped_paths = [
                (context_dir.parent / "terminology" / "config.yaml").resolve(),
                *[
                    (input_dir / "terminology" / "config.yaml").resolve()
                    for input_dir in self.input_dirs
                ],
            ]
            root_paths = [
                (input_dir / module_name / "config.yaml").resolve()
                for input_dir in self.input_dirs
            ]
            return [*contextual_paths, *canonical_paths, *root_paths, *grouped_paths]

        if relation == "root":
            root_matches = [
                (input_dir / module_name / "config.yaml").resolve()
                for input_dir in self.input_dirs
            ]
            candidate_paths = {
                candidate.source_file.resolve()
                for candidate in self._configs_for_name(module_name)
                if candidate.source_file is not None
            }
            matches = [path for path in root_matches if path in candidate_paths]
            if len(matches) == 1:
                return [matches[0]]
            if not matches:
                # Historical bundles may contain their own scoped terminology.
                # An unversioned authoring scan still has one canonical location.
                terminology_matches = [
                    (input_dir / category / module_name / "config.yaml").resolve()
                    for input_dir in self.input_dirs
                    for category in ("terminology", "report_templates")
                ]
                terminology_matches.extend(
                    (input_dir / "terminology" / "config.yaml").resolve()
                    for input_dir in self.input_dirs
                )
                canonical_matches = [
                    path for path in terminology_matches if path in candidate_paths
                ]
                if len(canonical_matches) == 1:
                    return canonical_matches

        return []

    def _collect_module_closure(
        self,
        module_names: list[str],
        *,
        context_config: "KnowledgeBaseConfig | None" = None,
    ) -> tuple[dict[str, "KnowledgeBaseConfig"], list[str]]:
        """Resolve the transitive closure across dependency and module edges."""

        resolved: dict[str, KnowledgeBaseConfig] = {}
        visiting: set[str] = set()
        preferred_order: list[str] = []

        def visit(name: str, parent_config: "KnowledgeBaseConfig | None") -> None:
            if name in resolved:
                return
            if name in visiting:
                raise ValueError(
                    "Circular dependency or module reference detected while "
                    f"visiting '{name}'."
                )

            module_config = self.resolve_module_config(
                name,
                context_config=parent_config,
                relation=self._reference_relation(name, parent_config),
            )

            visiting.add(name)
            preferred_order.append(name)
            for dependency in module_config.depends_on:
                visit(dependency, module_config)
            for child_module in module_config.modules:
                visit(child_module, module_config)
            visiting.remove(name)
            resolved[name] = module_config

        for module_name in module_names:
            visit(module_name, context_config)

        return resolved, preferred_order

    def _reference_relation(
        self,
        module_name: str,
        context_config: "KnowledgeBaseConfig | None",
    ) -> Literal["root", "module", "dependency"]:
        """Classify a reference: requested directly, a listed child, or a dependency."""
        if context_config is None:
            return "root"
        if module_name in context_config.modules:
            return "module"
        return "dependency"
