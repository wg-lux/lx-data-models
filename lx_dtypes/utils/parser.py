from pathlib import Path
from typing import Any, Dict, List, cast

import yaml

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.models.knowledge_base import (
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    knowledge_base_models_lookup,
)


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def camel_to_snake(camel_str: str) -> str:
    snake_str = ""
    for char in camel_str:
        if char.isupper():
            if snake_str:
                snake_str += "_"
            snake_str += char.lower()
        else:
            snake_str += char
    return snake_str


def parse_shallow_object(
    file_path: Path, kb_module_name: str = str_unknown_factory()
) -> List[KB_MODELS]:
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(
            f"The provided path {file_path} does not exist or is not a file."
        )

    assert file_path.suffix == ".yaml" or file_path.suffix == ".yml", (
        "File must be a YAML file."
    )

    # each yaml file is a list of objects
    with file_path.open("r", encoding="utf-8") as f:
        data: List[Dict[str, Any]] = yaml.safe_load(f) or []

    assert isinstance(data, list), "YAML file must contain a list of objects."
    results: List[KB_MODELS] = list()
    for item in data:
        assert isinstance(item, dict), "Each item in the list must be a dictionary."

        target_model_name = item.get("model")
        assert target_model_name is not None, "Each item must have a 'model' field."
        target_model_name_camel = snake_to_camel(target_model_name)
        assert target_model_name_camel in KB_MODEL_NAMES_ORDERED, (
            f"Unknown model name: {target_model_name_camel}"
        )

        assert target_model_name_camel in knowledge_base_models_lookup, (
            f"Unknown model type: {target_model_name_camel}"
        )

        _TargetModel = knowledge_base_models_lookup.get(target_model_name_camel)
        TargetModel = cast(type[KB_MODELS], _TargetModel)

        item.pop("model")  # remove the model field before validation
        item["kb_module_name"] = kb_module_name  # set the kb_module for reference
        item["source_file"] = file_path  # set source_file for reference
        result = TargetModel.model_validate(item)

        results.append(result)
    return results
