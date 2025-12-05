from pathlib import Path
from typing import Dict, List, Set

from pydantic import Field

from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase
from lx_dtypes.models.knowledge_base.knowledge_base_config import KnowledgeBaseConfig
from lx_dtypes.utils.dataloader import resolve_kb_module_load_order
from lx_dtypes.utils.mixins import BaseModelMixin


def _default_dataloader_dirs_factory():
    return [Path("./data/")]


class DataLoader(BaseModelMixin):
    """Model representing a data loader configuration."""

    # override name field to automatically yield a fixed name
    name: str = "data_loader"
    input_dirs: List[Path] = Field(default_factory=_default_dataloader_dirs_factory)
    module_configs: Dict[str, KnowledgeBaseConfig] = Field(default_factory=dict)

    def generate_knowledge_base(self, module_name: str) -> "KnowledgeBase":
        """Load a module configuration by name.

        Args:
            module_name (str): The name of the module to load.

        Returns:
            KnowledgeBaseConfig: The loaded module configuration.
        """
        from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase

        result = KnowledgeBase(name=module_name)
        if not self.module_configs:
            self.load_module_configs()

        # main_config = self.get_initialized_config(module_name)

        return result

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

    def load_module_configs(self):
        """Resolve the load order of modules based on dependencies.

        Returns:
            List[str]: Ordered list of module names to load.
        """
        from lx_dtypes.models.knowledge_base.knowledge_base_config import KnowledgeBaseConfig

        config_files = self.fetch_config_yamls()
        for config_file in config_files:
            kb_config = KnowledgeBaseConfig.from_yaml_file(config_file)
            self.module_configs[kb_config.name] = kb_config

    def get_initialized_config(self, module_name: str) -> "KnowledgeBaseConfig":
        """Return the configuration with modules ordered by dependency graph."""

        stored_config = self.module_configs.get(module_name)
        if stored_config is None:
            raise ValueError(f"Module '{module_name}' is not loaded. Call 'load_module_configs' first.")

        kb_config = stored_config.model_copy(deep=True)

        # Preserve declared order but ensure dependencies are placed ahead of dependents.
        requested_modules = list(dict.fromkeys([*kb_config.depends_on, *kb_config.modules]))
        if not requested_modules:
            return kb_config

        temp_module_dict = self._collect_modules_with_dependencies(requested_modules)
        load_order = resolve_kb_module_load_order(temp_module_dict, requested_modules)
        kb_config.modules = load_order
        return kb_config

    def _collect_modules_with_dependencies(self, module_names: List[str]) -> Dict[str, "KnowledgeBaseConfig"]:
        """Return all module configs reachable from ``module_names`` via depends_on graph."""

        resolved: Dict[str, KnowledgeBaseConfig] = {}
        visiting: Set[str] = set()

        def visit(name: str):
            if name in resolved:
                return
            if name in visiting:
                raise ValueError(f"Circular dependency detected while visiting '{name}'.")

            dependency_config = self.module_configs.get(name)
            if dependency_config is None:
                raise ValueError(f"Module '{name}' is referenced but no configuration was loaded for it.")

            visiting.add(name)
            for dependency in dependency_config.depends_on:
                visit(dependency)
            visiting.remove(name)
            resolved[name] = dependency_config

        for module_name in module_names:
            visit(module_name)

        return resolved
