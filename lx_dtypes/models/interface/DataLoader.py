from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
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
    input_dirs: list[Path] = Field(default_factory=_default_dataloader_dirs_factory)
    module_configs: dict[str, "KnowledgeBaseConfig"] = Field(default_factory=dict)
    module_config_candidates: dict[str, list["KnowledgeBaseConfig"]] = Field(
        default_factory=dict
    )

    def load_knowledge_base(self, module_name: str) -> "KnowledgeBase":
        """
        Assemble a KnowledgeBase for the given module name including its declared submodules.

        Returns:
            KnowledgeBase: The assembled knowledge base configured for the requested module with its ordered submodules imported.
        """
        from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

        if not self.module_configs:
            self.load_module_configs()

        kb_config = self._get_initialized_config(module_name)
        # Load root module data from YAML so the base KB is populated even when
        # there are no submodules.
        kb = KnowledgeBase.create_from_config(kb_config)

        ordered_submodules = kb_config.modules

        for sm_name in ordered_submodules:
            sm_config = self._get_initialized_config(
                sm_name,
                context_config=kb_config,
                relation="module",
            )
            sm_kb = KnowledgeBase.create_from_config(sm_config)
            kb.import_knowledge_base(sm_kb)
        return kb

    def fetch_config_yamls(self) -> list[Path]:
        """Screens the input directories to ensure they exist.
        Then recursively iterates all directories to the end to locate all
        files named 'config.yaml'.

        Returns:
            List[Path]: A list of existing config_files.
        """
        config_files: list[Path] = []
        for input_dir in self.input_dirs:
            if not input_dir.exists() or not input_dir.is_dir():
                continue

            config_files.extend(input_dir.rglob("config.yaml"))

        return config_files

    def load_module_configs(self) -> None:
        """
        Load KnowledgeBaseConfig objects from discovered config YAMLs into the loader's module_configs.

        Discovers all "config.yaml" files under the DataLoader's input_dirs, loads each file into a KnowledgeBaseConfig, sets the config's data.source_file to the file path, normalizes data paths relative to that file, and stores the config in self.module_configs keyed by the config's name.
        """

        config_files = sorted(
            {config_file.resolve() for config_file in self.fetch_config_yamls()}
        )
        self.module_configs = {}
        self.module_config_candidates = {}
        for config_file in config_files:
            kb_config = KnowledgeBaseConfig.from_yaml_file(config_file)
            kb_config.data.source_file = config_file
            kb_config.normalize_data_paths(config_file)
            self.module_config_candidates.setdefault(kb_config.name, []).append(
                kb_config
            )
            self.module_configs[kb_config.name] = kb_config

    def get_initialized_config(self, module_name: str) -> "KnowledgeBaseConfig":
        """Return the configuration with modules ordered by dependency graph."""

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

        stored_config = self._resolve_module_config(
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
        candidates = self.module_config_candidates.get(module_name)
        if candidates:
            return candidates

        legacy_config = self.module_configs.get(module_name)
        return [legacy_config] if legacy_config is not None else []

    def _resolve_module_config(
        self,
        module_name: str,
        *,
        context_config: "KnowledgeBaseConfig | None" = None,
        relation: Literal["root", "module", "dependency"] = "root",
    ) -> "KnowledgeBaseConfig":
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
                (input_dir / "terminology" / module_name / "config.yaml").resolve()
                for input_dir in self.input_dirs
            ]
            return [*contextual_paths, *canonical_paths]

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

            module_config = self._resolve_module_config(
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
        if context_config is None:
            return "root"
        if module_name in context_config.modules:
            return "module"
        return "dependency"
