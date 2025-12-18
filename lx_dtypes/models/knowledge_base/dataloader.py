from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Set

from pydantic import Field

from lx_dtypes.models.base_models.base_model import AppBaseModelNamesUUIDTags
from lx_dtypes.models.knowledge_base.knowledge_base_config import KnowledgeBaseConfig
from lx_dtypes.utils.dataloader import resolve_kb_module_load_order

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase


def _default_dataloader_dirs_factory() -> List[Path]:
    return [Path("./data/")]


class DataLoader(AppBaseModelNamesUUIDTags):
    """Model representing a data loader configuration."""

    # override name field to automatically yield a fixed name
    name: str = "data_loader"
    input_dirs: List[Path] = Field(default_factory=_default_dataloader_dirs_factory)
    module_configs: Dict[str, KnowledgeBaseConfig] = Field(default_factory=dict)

    def load_knowledge_base(self, module_name: str) -> "KnowledgeBase":
        """Load a knowledge base by module name.

        Args:
            module_name (str): The name of the knowledge base module to load.

        Returns:
            KnowledgeBase: The loaded knowledge base.
        """
        from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase

        kb_config = self.get_initialized_config(module_name)
        kb = KnowledgeBase(name=kb_config.name, config=kb_config)

        ordered_submodules = kb_config.modules

        for sm_name in ordered_submodules:
            sm_config = self.get_initialized_config(sm_name)
            sm_kb = KnowledgeBase.create_from_config(sm_config)
            kb.import_knowledge_base(sm_kb)
        return kb

    def fetch_config_yamls(self) -> List[Path]:
        """Screens the input directories to ensure they exist.
        Then recursively iterates all directories to the end to locate all
        files named 'config.yaml'.

        Returns:
            List[Path]: A list of existing config_files.
        """
        config_files: List[Path] = []
        for input_dir in self.input_dirs:
            if not input_dir.exists() or not input_dir.is_dir():
                continue

            for path in input_dir.rglob("config.yaml"):
                config_files.append(path)

        return config_files

    def load_module_configs(self) -> None:
        """Resolve the load order of modules based on dependencies.

        Returns:
            List[str]: Ordered list of module names to load.
        """
        from lx_dtypes.models.knowledge_base.knowledge_base_config import (
            KnowledgeBaseConfig,
        )

        config_files = self.fetch_config_yamls()
        for config_file in config_files:
            kb_config = KnowledgeBaseConfig.from_yaml_file(config_file)
            kb_config.data.source_file = config_file
            kb_config.normalize_data_paths(config_file)
            self.module_configs[kb_config.name] = kb_config

    def get_initialized_config(self, module_name: str) -> "KnowledgeBaseConfig":
        """Return the configuration with modules ordered by dependency graph."""

        stored_config = self.module_configs.get(module_name)
        if stored_config is None:
            raise ValueError(
                f"Module '{module_name}' is not loaded. Call 'load_module_configs' first."
            )

        kb_config = stored_config.model_copy(deep=True)

        # Preserve declared order but ensure dependencies are placed ahead of dependents.
        requested_modules = list(
            dict.fromkeys([*kb_config.depends_on, *kb_config.modules])
        )
        if not requested_modules:
            return kb_config

        expanded_modules = self._expand_module_hierarchy(requested_modules)

        temp_module_dict = self._collect_modules_with_dependencies(expanded_modules)
        load_order = resolve_kb_module_load_order(temp_module_dict, expanded_modules)
        kb_config.modules = load_order
        return kb_config

    def _expand_module_hierarchy(self, module_names: List[str]) -> List[str]:
        """Return a flattened list of modules including nested declarations."""

        expanded: List[str] = []
        seen: Set[str] = set()

        def visit(name: str) -> None:
            if name in seen:
                return
            seen.add(name)
            expanded.append(name)

            nested_config = self.module_configs.get(name)
            if nested_config is None:
                raise ValueError(f"Module '{name}' is referenced but not loaded.")

            for child_name in nested_config.modules:
                visit(child_name)

        for module_name in module_names:
            visit(module_name)

        return expanded

    def _collect_modules_with_dependencies(
        self, module_names: List[str]
    ) -> Dict[str, "KnowledgeBaseConfig"]:
        """Return all module configs reachable from ``module_names`` via depends_on graph."""

        resolved: Dict[str, KnowledgeBaseConfig] = {}
        visiting: Set[str] = set()

        def visit(name: str) -> None:
            if name in resolved:
                return
            if name in visiting:
                raise ValueError(
                    f"Circular dependency detected while visiting '{name}'."
                )

            dependency_config = self.module_configs.get(name)
            if dependency_config is None:
                raise ValueError(
                    f"Module '{name}' is referenced but no configuration was loaded for it."
                )

            visiting.add(name)
            for dependency in dependency_config.depends_on:
                visit(dependency)
            visiting.remove(name)
            resolved[name] = dependency_config

        for module_name in module_names:
            visit(module_name)

        return resolved
