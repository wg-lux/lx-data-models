import os
from pathlib import Path

import django

# Ensure the Django app config is loaded when this script is invoked standalone.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lx_dtypes.django_settings")
django.setup()

from lx_dtypes.models.interface.DataLoader import DataLoader  # noqa: E402
from lx_dtypes.models.interface.examples import (  # noqa: E402
    build_demo_star_upper_gi_export_paths,
    build_star_upper_gi_demo_interface,
)
from lx_dtypes.utils.dataframe import interface2dataset  # noqa: E402

DATA_DIRECTORIES = [Path("./demo-data/")]
DEMO_OUTPUTS = build_demo_star_upper_gi_export_paths(Path("./temp/generated_exports"))
DEMO_OUTPUTS.dataset_dir.mkdir(parents=True, exist_ok=True)


######### DB INTERFACE SETUP ###########
# Initialize the DataLoader with the specified data directories
dataloader = DataLoader(input_dirs=DATA_DIRECTORIES)

# Scan the directories for all available config.yaml files
dataloader.load_module_configs()

# Initialize the KnowledgeBaseConfig "star_upper_gi"
kb_config = dataloader.get_initialized_config("star_upper_gi")

# Retrieve the KnowledgeBase "star_upper_gi"
kb = dataloader.load_knowledge_base("star_upper_gi")

kb.to_yaml(DEMO_OUTPUTS.knowledge_base_yaml)
db_interface = build_star_upper_gi_demo_interface(kb)

# EXPERIMENTAL: Export CSV Files
# Will currently throw UserWarnings for empty dataframes
dataset = interface2dataset(db_interface)
dataset.to_csvs(DEMO_OUTPUTS.dataset_dir)
dataset.to_xlsx(DEMO_OUTPUTS.dataset_xlsx, overwrite=True)

db_interface.to_yaml(DEMO_OUTPUTS.interface_yaml)
