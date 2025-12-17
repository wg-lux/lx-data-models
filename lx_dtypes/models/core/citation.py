from lx_dtypes.models.core.citation_shallow import (
    CitationShallow,
    CitationShallowDataDict,
)


class CitationDataDict(CitationShallowDataDict):
    pass


class Citation(CitationShallow):
    """Rich representation of a bibliographic citation."""

    @property
    def ddict(self) -> type[CitationDataDict]:
        return CitationDataDict

    def to_ddict(self) -> CitationDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
