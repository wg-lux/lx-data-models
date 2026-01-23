import pytest

from lx_dtypes.utils.testing import validate_django_fixture

from ..Citation import Citation
from ..CitationDjango import CitationDjango


@pytest.mark.django_db
class TestCitationFixtures:
    def test_citation_fixture(self, citation_fixture: Citation) -> None:
        assert isinstance(citation_fixture, Citation)

    def test_django_citation_fixture(
        self, django_citation_fixture: CitationDjango
    ) -> None:
        validate_django_fixture(django_citation_fixture)
