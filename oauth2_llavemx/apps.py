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
        custom_step = "oauth2_llavemx.pipeline.associate_by_curp"
        anchor_step = "social_core.pipeline.user.create_user"

        pipeline = getattr(settings, "SOCIAL_AUTH_PIPELINE", None)

        if not pipeline:
            logger.warning(
                "[LlaveMX] SOCIAL_AUTH_PIPELINE no definido; no se puede parchear."
            )
            return

        # Asegurarnos de tener una lista mutable que todos compartan
        if isinstance(pipeline, tuple):
            pipeline = list(pipeline)
            setattr(settings, "SOCIAL_AUTH_PIPELINE", pipeline)

        if not isinstance(pipeline, list):
            logger.warning(
                "[LlaveMX] SOCIAL_AUTH_PIPELINE no es list (%s): %r",
                type(pipeline),
                pipeline,
            )
            return

        # Ya está insertado → no hacemos nada
        if custom_step in pipeline:
            logger.info(
                "[LlaveMX] Paso '%s' ya presente en SOCIAL_AUTH_PIPELINE. No se modifica.",
                custom_step,
            )
            return

        try:
            idx = pipeline.index(anchor_step)
            pipeline.insert(idx, custom_step)
            logger.info(
                "[LlaveMX] Paso '%s' insertado antes de '%s' en índice %s.",
                custom_step,
                anchor_step,
                idx,
            )
        except ValueError:
            # Si por alguna razón no está el anchor, lo ponemos al final
            pipeline.append(custom_step)
            logger.info(
                "[LlaveMX] Anchor '%s' no encontrado. Paso '%s' añadido al final.",
                anchor_step,
                custom_step,
            )
