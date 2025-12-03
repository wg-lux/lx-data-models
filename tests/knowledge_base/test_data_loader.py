from pathlib import Path

from icecream import ic

from lx_dtypes.models.base_models.path import FilesAndDirsModel
from lx_dtypes.models.knowledge_base import DataLoader

MAIN_KNOWLEDGE_BASE_CONFIG_FILE_PATH = Path("./lx_dtypes/data/sample_knowledge_base/config.yaml")


class TestDataLoader:
    def test_data_loader_fetch_config_yamls(self):
        kb_config = DataLoader(input_dirs=[Path("./lx_dtypes/data/sample_knowledge_base/")])
        data_loader = kb_config

        config_files = data_loader.fetch_config_yamls()
