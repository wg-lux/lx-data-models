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
from lx_dtypes.models.interface.data_roots import resolve_default_data_root


data_dir = resolve_default_data_root()
assert data_dir is not None

output_root = Path("./temp/generated_exports")
output_root.mkdir(parents=True, exist_ok=True)

######### DB INTERFACE SETUP ###########
# Initialize the DataLoader with the specified data directories
dataloader = DataLoader(
    input_dirs=[data_dir]
)


# Scan the directories for all available config.yaml files
kb_config = dataloader.get_initialized_config("star_upper_gi")
kb = dataloader.load_knowledge_base("star_upper_gi")

# Export generated artifacts separately from canonical source data.
kb.to_yaml(output_root / "knowledge_base.yaml")
db_interface = build_star_upper_gi_demo_interface(kb)

# EXPERIMENTAL: Export CSV Files
# Will currently throw UserWarnings for empty dataframes
dataset = interface2dataset(db_interface)
dataset.to_csvs(output_root / "standardized_dataset")
dataset.to_xlsx(output_root / "dataset.xlsx", overwrite=True)
db_interface.to_yaml(output_root / "db_interface.yaml")
