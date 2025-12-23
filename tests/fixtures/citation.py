from lx_dtypes.lx_django.models.core.citation import (
    Citation as DjangoCitationModel,
)
from pytest import fixture

from lx_dtypes.models.core.citation import Citation


@fixture
def sample_citation() -> Citation:
    return Citation(
        name="Sample Citation",
        citation_key="Doe2024Sample",
        title="A Sample Citation for Testing",
        abstract="This is a sample abstract for the citation used in testing.",
        authors=["John Doe", "Jane Smith"],
        publication_year=2024,
        journal="Journal of Testing",
        doi="10.1234/sample.doi",
        url="https://example.com/sample-citation",
        keywords=["testing", "sample", "citation"],
    )


@fixture(scope="function")
def sample_django_citation(sample_citation: Citation) -> DjangoCitationModel:
    ddict = sample_citation.to_ddict_shallow()
    django_citation = DjangoCitationModel.sync_from_ddict_shallow(ddict)
    django_citation.refresh_from_db()
    return django_citation
