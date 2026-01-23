from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel


def default_data_model_factory() -> FilesAndDirsModel:
    """
    Create a new data model instance populated with default values.

    Returns:
        FilesAndDirsModel: A new FilesAndDirsModel instance initialized with its defaults.
    """
    return FilesAndDirsModel()
