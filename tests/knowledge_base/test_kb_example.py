from typing import Callable

from lx_dtypes.models.knowledge_base import DataLoader
from lx_dtypes.utils.logging import Log
from lx_dtypes.utils.parser import parse_shallow_object


class TestKnowledgeBaseModel:
    def test_load_default_kb(self, yaml_data_loader: DataLoader, demo_kb_config_name: str, log_writer: Callable[..., Log]):
        kb_config = yaml_data_loader.get_initialized_config(demo_kb_config_name)
        module_names = kb_config.modules
        assert len(module_names) > 0
        msg = "\n-------------START OF KNOWLEDGE BASE MODULES PARSING LOG--------------\n"
        msg += f"Knowledge Base '{demo_kb_config_name}' loading with modules: {module_names}\n"

        # logger.log(kb_config.model_dump_json())
        source_file = kb_config.source_file
        assert source_file is not None
        # log_writer(f"Knowledge Base '{demo_kb_config_name}' source file: {source_file}")

        for i, module_name in enumerate(module_names):
            module_config = yaml_data_loader.get_initialized_config(module_name)
            assert module_config is not None

            submodule_files = module_config.data.get_files_with_suffix(".yaml")

            for sm_file in submodule_files:
                parsed_object_generator = parse_shallow_object(sm_file)
                sample = [_ for _ in parsed_object_generator]
                assert len(sample) > 0
                msg += f"  - Parsed object from {sm_file}: {sample}\n"

        log_writer(f"Knowledge Base '{demo_kb_config_name}' modules parsed:\n{msg}")
