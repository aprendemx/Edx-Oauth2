from django.apps import AppConfig
from django.conf import settings


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX"

    def ready(self):
        """
        Inserta associate_by_curp en el pipeline REAL usado por Open edX.

        - Funciona en LMS, CMS y Celery.
        - No usa monkeypatch (evita Apps aren't loaded yet).
        - Respeta el pipeline ya generado por third_party_auth.apply_settings.
        """

        pipeline = list(getattr(settings, "SOCIAL_AUTH_PIPELINE", []))
        custom = "oauth2_llavemx.pipeline.associate_by_curp"

        if not pipeline or custom in pipeline:
            return

        # Paso real que existe en Open edX (NO el de social_core)
        anchor = "common.djangoapps.third_party_auth.pipeline.social_user"

        if anchor in pipeline:
            idx = pipeline.index(anchor)
            pipeline.insert(idx + 1, custom)
        else:
            # fallback defensivo
            pipeline.append(custom)

        settings.SOCIAL_AUTH_PIPELINE = pipeline
        settings.THIRD_PARTY_AUTH_PIPELINE = list(pipeline)
