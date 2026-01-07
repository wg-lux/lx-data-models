from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel


def default_data_model_factory() -> FilesAndDirsModel:
    return FilesAndDirsModel()
