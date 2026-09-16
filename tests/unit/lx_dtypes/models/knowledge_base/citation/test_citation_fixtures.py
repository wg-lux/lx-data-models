import pytest

from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.citation.CitationDjango import CitationDjango
from lx_dtypes.utils.testing import validate_django_fixture


@pytest.mark.django_db
class TestCitationFixtures:
    def test_citation_fixture(self, citation_fixture: Citation) -> None:
        assert isinstance(citation_fixture, Citation)

    def test_django_citation_fixture(
        self, django_citation_fixture: CitationDjango
    ) -> None:
        validate_django_fixture(django_citation_fixture)
