from django.apps import AppConfig
from django.conf import settings

class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX"

    def ready(self):
        """
        Inserta associate_by_curp DESPUÉS de third_party_auth.apply_settings,
        garantizando que nuestro paso no se pierda.
        """
        from common.djangoapps.third_party_auth import settings as tpa_settings

        original_apply = tpa_settings.apply_settings

        def wrapped_apply(django_settings):
            # Ejecutar configuración original
            original_apply(django_settings)

            pipeline = list(getattr(django_settings, "SOCIAL_AUTH_PIPELINE", []))
            anchor = "social_core.pipeline.social_auth.social_user"
            step = "oauth2_llavemx.pipeline.associate_by_curp"

            if step not in pipeline:
                if anchor in pipeline:
                    pipeline.insert(pipeline.index(anchor) + 1, step)
                else:
                    pipeline.append(step)

            django_settings.SOCIAL_AUTH_PIPELINE = pipeline
            django_settings.THIRD_PARTY_AUTH_PIPELINE = list(pipeline)

        # Monkeypatch correcto
        tpa_settings.apply_settings = wrapped_apply
