import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX Integration"
    _pipeline_patched = False
    _context_patched = False

    def ready(self):
        try:
            self._inject_pipeline_step()
            self._patch_mfe_context()
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

    def _patch_mfe_context(self):
        """
        Parche para que el MFE reciba todos los campos de LlaveMX en pipelineUserDetails.

        Dos parches:
        1. get_auth_context / get_mfe_context: si pipeline_user_details viene vacío,
           usar llavemx_details de sesión como fallback.
        2. ContextDataSerializer.get_pipelineUserDetails: passthrough completo del dict
           para que lleguen los campos custom (curp, nombres, etc.) sin filtrado.
        """
        if self._context_patched:
            return

        try:
            from openedx.core.djangoapps.user_authn.views import utils as auth_utils

            def _with_llavemx_fallback(fn):
                def wrapper(request, *args, **kwargs):
                    context = fn(request, *args, **kwargs)
                    if not context:
                        return context
                    pud = context.get("pipeline_user_details") or {}
                    if not pud:
                        session_details = (getattr(request, "session", {}) or {}).get("llavemx_details") or {}
                        if session_details:
                            context["pipeline_user_details"] = session_details
                            context.setdefault("currentProvider", "llavemx")
                    return context
                return wrapper

            auth_utils.get_auth_context = _with_llavemx_fallback(auth_utils.get_auth_context)
            auth_utils.get_mfe_context = _with_llavemx_fallback(auth_utils.get_mfe_context)
            logger.info("[LlaveMX] Parche aplicado a get_auth_context / get_mfe_context.")

        except Exception:
            logger.exception("[LlaveMX] No se pudo parchear MFE context utils.")

        try:
            from openedx.core.djangoapps.user_authn.serializers import ContextDataSerializer

            def _pipeline_user_details_passthrough(self, obj):
                return obj.get("pipeline_user_details") or {}

            ContextDataSerializer.get_pipelineUserDetails = _pipeline_user_details_passthrough
            logger.info("[LlaveMX] Parche aplicado a ContextDataSerializer.get_pipelineUserDetails.")
            self._context_patched = True

        except Exception:
            logger.exception("[LlaveMX] No se pudo parchear ContextDataSerializer.")
