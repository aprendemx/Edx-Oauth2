import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX Integration"

    def ready(self):
        """
        Inserta associate_by_curp en el pipeline REAL usado por Open edX,
        modificando la lista *en sitio* (sin reemplazar el objeto).
        """
        self._inject_pipeline_step()

def _inject_pipeline_step(self):
    import common.djangoapps.third_party_auth.pipeline as tpa_pipeline
    from django.conf import settings
    import logging

    logger = logging.getLogger(__name__)

    custom_step = "oauth2_llavemx.pipeline.associate_by_curp"
    anchor = "common.djangoapps.third_party_auth.pipeline.ensure_user_information"

    # --- 1. Patch SOCIAL_AUTH_PIPELINE (settings) ---
    try:
        pipeline = list(settings.SOCIAL_AUTH_PIPELINE)
        if custom_step not in pipeline:
            idx = pipeline.index("social_core.pipeline.user.create_user")
            pipeline.insert(idx, custom_step)
            setattr(settings, "SOCIAL_AUTH_PIPELINE", pipeline)
            logger.info("[LlaveMX] Patch SOCIAL_AUTH_PIPELINE successful.")
    except Exception as e:
        logger.error(f"[LlaveMX] Error patching SOCIAL_AUTH_PIPELINE: {e}")

    # --- 2. Patch THIRD_PARTY_AUTH pipeline (internal module) ---
    try:
        pipeline = list(tpa_pipeline.AUTH_PIPELINE)
        if custom_step not in pipeline:
            idx = pipeline.index(anchor)
            pipeline.insert(idx + 1, custom_step)
            tpa_pipeline.AUTH_PIPELINE = pipeline
            logger.info("[LlaveMX] Patch THIRD_PARTY_AUTH pipeline successful.")
    except Exception as e:
        logger.error(f"[LlaveMX] Error patching THIRD_PARTY_AUTH pipeline: {e}")
