from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX Integration"

    def ready(self):
        """
        Punto de entrada para modificar el pipeline después de que TPA
        haya aplicado su configuración por defecto.
        """
        self._inject_pipeline_step()

    def _inject_pipeline_step(self):
        """
        Inserta el paso 'associate_by_curp' en TODOS los pipelines relevantes.
        - SOCIAL_AUTH_PIPELINE   → usado por PSA + TPA
        - THIRD_PARTY_AUTH_PIPELINE → usado por Open edX en flujos LMS/MFE
        """

        custom_step = "oauth2_llavemx.pipeline.associate_by_curp"
        anchor_step = "social_core.pipeline.user.create_user"

        # Pipelines que Open edX realmente usa
        pipelines_to_patch = [
            "SOCIAL_AUTH_PIPELINE",
            "THIRD_PARTY_AUTH_PIPELINE",
        ]

        for pipeline_name in pipelines_to_patch:
            pipeline = getattr(settings, pipeline_name, None)

            if not pipeline:
                # El pipeline no existe en este contexto → ignorar
                continue

            # Convertir a lista editable
            pipeline_list = list(pipeline)

            # Evitar duplicados en reinicios o re-importación
            if custom_step in pipeline_list:
                continue

            # Insertar justo antes de create_user
            if anchor_step in pipeline_list:
                idx = pipeline_list.index(anchor_step)
                pipeline_list.insert(idx, custom_step)
            else:
                # Si por alguna razón no está el anchor, hacemos fallback seguro
                pipeline_list.append(custom_step)

            # Aplicar
            setattr(settings, pipeline_name, pipeline_list)

            # Log interno (no print, seguro en Celery/uWSGI)
            logger.info(
                f"[LlaveMX] Paso '{custom_step}' inyectado en '{pipeline_name}' "
                f"antes de '{anchor_step}'"
                if anchor_step in pipeline_list else
                f"[LlaveMX] Paso '{custom_step}' agregado al final de '{pipeline_name}'"
            )
