from django.apps import AppConfig
from django.conf import settings


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX"

    def ready(self):
        """
        Inserts the CURP association step right after the default social_user
        pipeline stage if it is not already present.
        """
        pipeline = list(getattr(settings, "SOCIAL_AUTH_PIPELINE", []))
        target = "social_core.pipeline.social_auth.social_user"
        custom = "oauth2_llavemx.pipeline.associate_by_curp"

        if not pipeline or custom in pipeline:
            return

        try:
            idx = pipeline.index(target)
        except ValueError:
            return

        pipeline.insert(idx + 1, custom)
        settings.SOCIAL_AUTH_PIPELINE = pipeline
