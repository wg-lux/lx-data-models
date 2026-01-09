import pytest

from ..Citation import Citation
from ..CitationDjango import CitationDjango


@pytest.mark.django_db
class TestCitationFixtures:
    def test_citation_fixture(self, citation_fixture: Citation) -> None:
        assert isinstance(citation_fixture, Citation)

    def test_django_citation_fixture(
        self, django_citation_fixture: CitationDjango
    ) -> None:
        assert isinstance(django_citation_fixture, CitationDjango)

        _ddict = django_citation_fixture.ddict
        assert _ddict["uuid"] == str(django_citation_fixture.uuid)

        list_type_fields = django_citation_fixture.list_type_fields()
        for field in list_type_fields:
            value = getattr(django_citation_fixture, field)
            assert isinstance(value, list)

            value_from_ddict = _ddict.get(field, [])
            assert isinstance(value_from_ddict, list)
