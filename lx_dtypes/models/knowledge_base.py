from heapq import heappop, heappush
from pathlib import Path
from typing import Dict, List, Set, Tuple

from pydantic import Field

from lx_dtypes.models.base_models.path import FilesAndDirsModel
from lx_dtypes.utils.mixins import BaseModelMixin, TaggedBaseModelMixin


def _default_dataloader_dirs_factory():
    return [Path("./data/")]


def _default_data_model_factory():
    return FilesAndDirsModel()


def _default_empty_list_factory():
    _list: List[str] = []
    return _list


class KnowledgeBaseConfig(BaseModelMixin, TaggedBaseModelMixin):
    """Model representing a knowledge base configuration."""

    depends_on: list[str] = Field(default_factory=_default_empty_list_factory)
    modules: List[str] = Field(default_factory=_default_empty_list_factory)
    data: FilesAndDirsModel = Field(default_factory=_default_data_model_factory)
    version: str
    # dependency_graph: # TODO


class DataLoader(BaseModelMixin):
    """Model representing a data loader configuration."""

    # override name field to automatically yield a fixed name
    name: str = "data_loader"
    input_dirs: List[Path] = Field(default_factory=_default_dataloader_dirs_factory)
    module_configs: Dict[str, "KnowledgeBaseConfig"] = Field(default_factory=dict)

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
        config_files = self.fetch_config_yamls()
        for config_file in config_files:
            kb_config = KnowledgeBaseConfig.from_yaml_file(config_file)
            self.module_configs[kb_config.name] = kb_config

    def get_initialized_config(self, module_name: str) -> KnowledgeBaseConfig:
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
        load_order = self._resolve_module_load_order(temp_module_dict, requested_modules)
        kb_config.modules = load_order
        return kb_config

    def _collect_modules_with_dependencies(self, module_names: List[str]) -> Dict[str, KnowledgeBaseConfig]:
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

    def _resolve_module_load_order(
        self,
        modules: Dict[str, KnowledgeBaseConfig],
        preferred_order: List[str],
    ) -> List[str]:
        """Topologically sort modules while respecting preferred ordering when possible."""

        if not modules:
            return []

        adjacency: Dict[str, Set[str]] = {name: set() for name in modules}
        indegree: Dict[str, int] = {name: 0 for name in modules}

        for module_name, module_config in modules.items():
            for dependency in module_config.depends_on:
                if dependency not in modules:
                    raise ValueError(
                        f"Module '{module_name}' depends on '{dependency}', which was not collected for ordering.",
                    )
                adjacency[dependency].add(module_name)
                indegree[module_name] += 1

        preferred_index = {name: idx for idx, name in enumerate(preferred_order)}

        def priority(name: str) -> tuple[int, str]:
            return (preferred_index.get(name, len(preferred_index)), name)

        heap: List[Tuple[int, str]] = []
        for name, degree in indegree.items():
            if degree == 0:
                heappush(heap, priority(name))

        load_order: List[str] = []
        while heap:
            _, node = heappop(heap)
            load_order.append(node)
            for dependent in sorted(adjacency[node]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heappush(heap, priority(dependent))

        if len(load_order) != len(modules):
            unresolved = ", ".join(sorted(set(modules.keys()) - set(load_order)))
            raise ValueError(f"Circular dependency detected among modules: {unresolved}")

        return load_order
