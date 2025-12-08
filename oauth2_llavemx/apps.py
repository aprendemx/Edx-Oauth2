import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX Integration"

    def ready(self):
        """
        Inserta associate_by_curp en el pipeline real usado por Open edX.
        Se envuelve en try/except para evitar que LMS/CMS colapsen
        si algo falla durante la carga temprana.
        """
        try:
            self._inject_pipeline_step()
        except Exception:
            logger.exception("[LlaveMX] Error during pipeline injection")

    def _inject_pipeline_step(self):
        # Importación tardía: asegura que third_party_auth ya está cargado
        import common.djangoapps.third_party_auth.pipeline as tpa_pipeline

        custom_step = "oauth2_llavemx.pipeline.associate_by_curp"

        anchor_social = "social_core.pipeline.user.create_user"
        anchor_tpa = "common.djangoapps.third_party_auth.pipeline.ensure_user_information"

        # --- 1. Patch SOCIAL_AUTH_PIPELINE ---
        try:
            pipeline = list(getattr(settings, "SOCIAL_AUTH_PIPELINE", []))

            if pipeline and custom_step not in pipeline:
                if anchor_social in pipeline:
                    idx = pipeline.index(anchor_social)
                    pipeline.insert(idx, custom_step)
                else:
                    pipeline.append(custom_step)

                setattr(settings, "SOCIAL_AUTH_PIPELINE", pipeline)
                logger.info("[LlaveMX] SOCIAL_AUTH_PIPELINE patched successfully.")
        except Exception as e:
            logger.error(f"[LlaveMX] Error patching SOCIAL_AUTH_PIPELINE: {e}")

        # --- 2. Patch AUTH_PIPELINE interno de Third Party Auth ---
        try:
            if hasattr(tpa_pipeline, "AUTH_PIPELINE"):
                pipeline = list(tpa_pipeline.AUTH_PIPELINE)

                if custom_step not in pipeline:
                    if anchor_tpa in pipeline:
                        idx = pipeline.index(anchor_tpa)
                        pipeline.insert(idx + 1, custom_step)
                    elif anchor_social in pipeline:
                        idx = pipeline.index(anchor_social)
                        pipeline.insert(idx, custom_step)
                    else:
                        pipeline.append(custom_step)

                    tpa_pipeline.AUTH_PIPELINE = pipeline
                    logger.info("[LlaveMX] AUTH_PIPELINE patched successfully.")
            else:
                logger.warning("[LlaveMX] AUTH_PIPELINE not found to patch")
        except Exception as e:
            logger.error(f"[LlaveMX] Error patching AUTH_PIPELINE: {e}")
