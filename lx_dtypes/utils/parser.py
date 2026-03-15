from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, cast

import yaml
from pydantic import ValidationError

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.models.knowledge_base import (
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    knowledge_base_models_lookup,
)

MODEL_NAME_ALIASES: Dict[str, str] = {
    "finding_validator": "findings_validator",
}


@dataclass(frozen=True)
class ParsedYamlObject:
    parsed_object: KB_MODELS
    model_name_raw: str
    model_name: str
    source_file: Path
    line: int
    column: int


@dataclass(frozen=True)
class _YamlItemWithLocation:
    item: Dict[str, Any]
    line: int
    column: int


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


def normalize_model_name(model_name: str) -> str:
    return MODEL_NAME_ALIASES.get(model_name, model_name)


def _yaml_error_with_location(file_path: Path, exc: yaml.YAMLError) -> ValueError:
    problem_mark = getattr(exc, "problem_mark", None)
    if problem_mark is not None:
        line = int(problem_mark.line) + 1
        column = int(problem_mark.column) + 1
        return ValueError(f"{file_path}:{line}:{column}: {exc}")
    return ValueError(f"{file_path}:1:1: {exc}")


def _load_yaml_items_with_locations(file_path: Path) -> List[_YamlItemWithLocation]:
    raw_text = file_path.read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise _yaml_error_with_location(file_path, exc)

    if loaded is None:
        return []
    if not isinstance(loaded, list):
        raise ValueError(f"{file_path}:1:1: YAML file must contain a list of objects.")

    try:
        composed = yaml.compose(raw_text)
    except yaml.YAMLError as exc:
        raise _yaml_error_with_location(file_path, exc)

    if composed is None:
        return []
    if not isinstance(composed, yaml.SequenceNode):
        raise ValueError(f"{file_path}:1:1: YAML root must be a sequence.")

    located_items: List[_YamlItemWithLocation] = []
    for index, raw_item in enumerate(loaded):
        node = composed.value[index] if index < len(composed.value) else None
        line = int(node.start_mark.line) + 1 if node is not None else 1
        column = int(node.start_mark.column) + 1 if node is not None else 1
        if not isinstance(raw_item, dict):
            raise ValueError(
                f"{file_path}:{line}:{column}: Each item in the list must be a dictionary."
            )
        located_items.append(
            _YamlItemWithLocation(item=dict(raw_item), line=line, column=column)
        )
    return located_items


def parse_shallow_object(
    file_path: Path,
    kb_module_name: str = str_unknown_factory(),
    *,
    strict_model_aliases: bool = False,
) -> List[KB_MODELS]:
    """
    This method parses YAML files and returns a List of KnowledgeBase models.
    This is achieved by matching for string keys and filling the List with the fitting models.
    Input:
        - File Path
        - KnowledgeBase module name (optional will be inferred in case of default string literal "unknown".)
    Output:
        - List filled with KnowledgeBase models. Possible models in the list:
        Classification, ClassificationChoice, ClassificationChoiceDescriptor,
        Examination, Finding, FindingType, Indication, IndicationType, Intervention, InterventionType, Unit, UnitType,
        InformationSource, InformationSourceType, Citation
    """

    return [
        parsed_entry.parsed_object
        for parsed_entry in parse_shallow_object_with_meta(
            file_path,
            kb_module_name=kb_module_name,
            strict_model_aliases=strict_model_aliases,
        )
    ]


def parse_shallow_object_with_meta(
    file_path: Path,
    kb_module_name: str = str_unknown_factory(),
    *,
    strict_model_aliases: bool = False,
) -> List[ParsedYamlObject]:
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(
            f"The provided path {file_path} does not exist or is not a file."
        )

    if file_path.suffix not in {".yaml", ".yml"}:
        raise ValueError(f"{file_path}:1:1: File must be a YAML file.")

    located_items = _load_yaml_items_with_locations(file_path)
    results: List[ParsedYamlObject] = []

    for located_item in located_items:
        item = dict(located_item.item)
        target_model_name_raw = item.get("model")
        if not isinstance(target_model_name_raw, str) or target_model_name_raw == "":
            raise ValueError(
                f"{file_path}:{located_item.line}:{located_item.column}: "
                "Each item must have a non-empty string 'model' field."
            )

        target_model_name = normalize_model_name(target_model_name_raw)
        if strict_model_aliases and target_model_name != target_model_name_raw:
            raise ValueError(
                f"{file_path}:{located_item.line}:{located_item.column}: "
                f"Model alias '{target_model_name_raw}' is deprecated; "
                f"use '{target_model_name}'."
            )

        target_model_name_camel = snake_to_camel(target_model_name)
        if target_model_name_camel not in KB_MODEL_NAMES_ORDERED:
            raise ValueError(
                f"{file_path}:{located_item.line}:{located_item.column}: "
                f"Unknown model name '{target_model_name_camel}'."
            )

        if target_model_name_camel not in knowledge_base_models_lookup:
            raise ValueError(
                f"{file_path}:{located_item.line}:{located_item.column}: "
                f"Unknown model type '{target_model_name_camel}'."
            )

        _TargetModel = knowledge_base_models_lookup.get(target_model_name_camel)
        TargetModel = cast(type[KB_MODELS], _TargetModel)

        item.pop("model")
        item["kb_module_name"] = kb_module_name
        item["source_file"] = file_path
        try:
            parsed_object = TargetModel.model_validate(item)
        except ValidationError as exc:
            errors = exc.errors(include_url=False)
            first_error: dict[str, Any] = (
                dict(errors[0]) if errors else {"loc": (), "msg": "Validation error"}
            )
            err_loc = ".".join(str(part) for part in first_error.get("loc", ()))
            err_msg = str(first_error.get("msg", "Validation error"))
            err_detail = f" [{err_loc}] {err_msg}" if err_loc else f" {err_msg}"
            raise ValueError(
                f"{file_path}:{located_item.line}:{located_item.column}: "
                f"Invalid '{target_model_name}' entry.{err_detail}"
            ) from exc

        results.append(
            ParsedYamlObject(
                parsed_object=parsed_object,
                model_name_raw=target_model_name_raw,
                model_name=target_model_name,
                source_file=file_path,
                line=located_item.line,
                column=located_item.column,
            )
        )
    return results
