from typing import Callable

from lx_dtypes.models.knowledge_base import DataLoader
from lx_dtypes.utils.logging import Log


class TestKnowledgeBaseModel:
    def test_load_default_kb(self, yaml_data_loader: DataLoader, demo_kb_config_name: str, log_writer: Callable[..., Log]):
        kb_config = yaml_data_loader.get_initialized_config(demo_kb_config_name)
        module_names = kb_config.modules
        assert len(module_names) > 0

        log_writer(f"Knowledge Base '{demo_kb_config_name}' loaded with modules: {module_names}")

        # logger.log(kb_config.model_dump_json())
        source_file = kb_config.source_file
        assert source_file is not None
        # log_writer(f"Knowledge Base '{demo_kb_config_name}' source file: {source_file}")

        for i, module_name in enumerate(module_names):
            # msg = "\n"
            module_config = yaml_data_loader.get_initialized_config(module_name)
            assert module_config is not None

            submodule_files = module_config.data.get_files_with_suffix(".yaml")
            sm_str = [str(_f) for _f in submodule_files]
            sm_str = "\n".join(sm_str)
            if module_name == "information_source_data":
                log_writer(sm_str)
