from django.apps import AppConfig
import logging


class LxDtypesDjangoConfig(AppConfig):
    name = "lx_dtypes.django"
    label = "lx_dtypes_django"
    default_auto_field = "django.db.models.AutoField"
    logger = logging.getLogger(__name__)

    def ready(self) -> None:
        try:
            from .api.terminology_routes import ensure_default_terminology_registry

            ensure_default_terminology_registry()
        except Exception:
            self.logger.exception(
                "Failed to run terminology registry auto-seed during app startup."
            )
