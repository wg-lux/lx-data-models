from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

from pydantic import BaseModel

import lx_dtypes.models
from lx_dtypes.models.base.app_base_model.pydantic.field_safety import (
    direct_parent_field_collisions,
)
from lx_dtypes.models.base.app_base_model.pydantic.InterfaceMixIns import (
    ListFieldSerializationMixIn,
)
from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel
from lx_dtypes.models.base.file.pydantic.PathMixIn import PathMixin


def _model_modules() -> list[ModuleType]:
    modules: list[ModuleType] = []
    for module_info in pkgutil.walk_packages(
        lx_dtypes.models.__path__,
        f"{lx_dtypes.models.__name__}.",
    ):
        if ".tests" in module_info.name:
            continue
        modules.append(importlib.import_module(module_info.name))
    return modules


def _declared_pydantic_models() -> set[type[BaseModel]]:
    models: set[type[BaseModel]] = set()
    for module in _model_modules():
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, BaseModel)
                and value.__module__ == module.__name__
            ):
                models.add(value)
    return models


class _FirstListFields(ListFieldSerializationMixIn, BaseModel):
    first_values: str | list[str]

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return ["first_values"]


class _SecondListFields(ListFieldSerializationMixIn, BaseModel):
    second_values: str | list[str]

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return ["second_values"]


class _CombinedListFields(_FirstListFields, _SecondListFields):
    pass


class _CollisionParentA(BaseModel):
    shared_field: str


class _CollisionParentB(BaseModel):
    shared_field: str


class _SyntheticCollision(_CollisionParentA, _CollisionParentB):
    pass


def test_list_field_serialization_aggregates_all_mro_declarations() -> None:
    model = _CombinedListFields.model_validate(
        {
            "first_values": "one, two",
            "second_values": "three, four",
        }
    )

    assert model.first_values == ["one", "two"]
    assert model.second_values == ["three", "four"]
    assert model.model_dump()["first_values"] == "one,two"
    assert model.model_dump()["second_values"] == "three,four"


def test_duplicate_field_check_detects_direct_parent_collision() -> None:
    collisions = direct_parent_field_collisions(_SyntheticCollision)

    assert collisions == {
        "shared_field": (_CollisionParentA, _CollisionParentB),
    }


def test_repository_multi_parent_models_have_no_duplicate_direct_fields() -> None:
    collisions = {
        f"{model.__module__}.{model.__qualname__}": direct_parent_field_collisions(
            model
        )
        for model in _declared_pydantic_models()
        if len(
            [
                parent
                for parent in model.__bases__
                if isinstance(parent, type) and issubclass(parent, BaseModel)
            ]
        )
        > 1
        and direct_parent_field_collisions(model)
    }

    assert collisions == {}


def test_files_and_dirs_uses_minimal_inheritance_chain() -> None:
    assert FilesAndDirsModel.__bases__ == (PathMixin,)
