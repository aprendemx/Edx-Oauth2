import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX Integration"
    _pipeline_patched = False

    def ready(self):
        try:
            self._inject_pipeline_step()
        except Exception:
            logger.exception("[LlaveMX] Error during pipeline injection")

    def _inject_pipeline_step(self):
        if self._pipeline_patched:
            return

        custom_steps = [
            "oauth2_llavemx.pipeline.preserve_llavemx_details",
            "oauth2_llavemx.pipeline.associate_by_curp",
        ]

        # Target: antes de ensure_user_information para que los details completos
        # queden en el partial y se expongan a TPA/MFE.
        anchor_step = "common.djangoapps.third_party_auth.pipeline.ensure_user_information"

        # Fallback anchor if the above is missing
        fallback_anchor = "social_core.pipeline.user.create_user"

        try:
            # TPA sobreescribe SOCIAL_AUTH_PIPELINE, por lo que debemos editar esa lista.
            # Se convierte a list para evitar problemas de inmutabilidad si fuera tupla.
            current_pipeline = getattr(settings, "SOCIAL_AUTH_PIPELINE", [])
            pipeline = list(current_pipeline)

            # Insertar los pasos personalizados si no están presentes
            for step in reversed(custom_steps):
                if step in pipeline:
                    continue

                if anchor_step in pipeline:
                    idx = pipeline.index(anchor_step)
                    pipeline.insert(idx, step)
                    logger.info(f"[LlaveMX] Injected custom step BEFORE {anchor_step}: {step}")
                elif fallback_anchor in pipeline:
                    idx = pipeline.index(fallback_anchor)
                    pipeline.insert(idx, step)
                    logger.info(f"[LlaveMX] Injected custom step BEFORE {fallback_anchor}: {step}")
                else:
                    pipeline.append(step)
                    logger.warning("[LlaveMX] Anchors not found. Appended custom step to end.")

            setattr(settings, "SOCIAL_AUTH_PIPELINE", pipeline)
            logger.info("[LlaveMX] SOCIAL_AUTH_PIPELINE actualizado correctamente.")
            self._pipeline_patched = True

        except Exception as e:
            logger.error("[LlaveMX] Error al parchear SOCIAL_AUTH_PIPELINE: %s", e)
