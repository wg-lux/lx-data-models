from typing import Union

from lx_dtypes.models.knowledge_base import KB_MODELS_DJANGO
from lx_dtypes.models.ledger import L_MODELS_DJANGO


def validate_django_fixture(
    model_fixture: Union[KB_MODELS_DJANGO, L_MODELS_DJANGO],
) -> None:
    _ddict = model_fixture.ddict
    assert _ddict["uuid"] == model_fixture.uuid

    list_type_fields = model_fixture.list_type_fields()
    m2m_fields = model_fixture.m2m_fields()
    for field in list_type_fields:
        if field in m2m_fields:
            continue  # skip m2m fields here
        value = getattr(model_fixture, field)
        assert isinstance(value, str)

        value_from_ddict = _ddict.get(field, [])
        assert isinstance(value_from_ddict, list)

    for field in m2m_fields:
        value = getattr(model_fixture, field)
        assert hasattr(value, "all")  # m2m fields should have an 'all' method

        value_from_ddict = _ddict.get(field, [])
        assert isinstance(value_from_ddict, list)
