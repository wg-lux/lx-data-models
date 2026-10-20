from pathlib import Path

import pandas as pd
import pytest
from pandera.errors import SchemaError

from lx_dtypes.models.interface.examples import (
    build_demo_star_upper_gi_export_paths,
    build_star_upper_gi_demo_interface,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.stats.schemas.knowledge_base import (
    ClassificationChoiceDescriptorDfSchema,
)
from lx_dtypes.utils.dataframe import interface2dataset


def test_empty_export_preserves_required_column_validation() -> None:
    schema = ClassificationChoiceDescriptorDfSchema.to_schema()
    columns = list(ClassificationChoiceDescriptor.model_fields)
    empty = pd.DataFrame(columns=columns)
    assert schema.validate(empty).columns.tolist() == columns
    with pytest.raises(SchemaError, match="Missing columns"):
        schema.validate(empty.drop(columns=["name"]))


def test_populated_export_still_validates_records() -> None:
    schema = ClassificationChoiceDescriptorDfSchema.to_schema()
    record = ClassificationChoiceDescriptor(name="size").model_dump()
    assert len(schema.validate(pd.DataFrame([record]))) == 1
    record["classification_choice_descriptor_type"] = "invalid"
    with pytest.raises(SchemaError):
        schema.validate(pd.DataFrame([record]))


class TestStarUpperGIData:
    def test_star_upper_gi_data_loading(
        self, star_ugi_knowledge_base: KnowledgeBase, tmp_path: Path
    ) -> None:
        knowledge_base = star_ugi_knowledge_base
        assert knowledge_base.config.name == "star_upper_gi"

        export_paths = build_demo_star_upper_gi_export_paths(tmp_path)
        export_paths.dataset_dir.mkdir(parents=True, exist_ok=True)

        knowledge_base.to_yaml(export_paths.knowledge_base_yaml)
        db_interface = build_star_upper_gi_demo_interface(knowledge_base)

        dataset = interface2dataset(db_interface)
        dataset.to_csvs(export_paths.dataset_dir)
        dataset.to_xlsx(export_paths.dataset_xlsx, overwrite=True)
        db_interface.to_yaml(export_paths.interface_yaml)

        assert export_paths.knowledge_base_yaml.exists()
        assert export_paths.interface_yaml.exists()
        assert export_paths.dataset_xlsx.exists()
