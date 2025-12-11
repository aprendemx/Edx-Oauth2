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
        """
        Inserts associate_by_curp into the SOCIAL_AUTH_PIPELINE.
        We rely on the fact that TPA's settings are applied early, 
        so we modify the settings.SOCIAL_AUTH_PIPELINE list directly.
        """
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
            # TPA Overwrites SOCIAL_AUTH_PIPELINE, so we must edit THAT list.
            # We access it from django.conf.settings
            
            # We get the list object. IMPORTANT: We cast to list to avoid tuple immutability issues
            # though TPA sets it as a list hardcoded.
            current_pipeline = getattr(settings, "SOCIAL_AUTH_PIPELINE", [])
            
            # If it's a tuple, we must convert to list and RE-SET it. 
            # If it's a list, we can modify in place, but re-setting is safer.
            pipeline = list(current_pipeline)

            # Insert custom steps if missing
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

            # Apply the modified list back to settings
            setattr(settings, "SOCIAL_AUTH_PIPELINE", pipeline)
            logger.info("[LlaveMX] SOCIAL_AUTH_PIPELINE updated successfully.")
            self._pipeline_patched = True

        except Exception as e:
            logger.error(f"[LlaveMX] Failed to patch SOCIAL_AUTH_PIPELINE: {e}")

    def _patch_mfe_context(self):
        """
        Parche pequeño para que, si el pipeline_user_details viene vacío,
        pero la sesión trae llavemx_details, el MFE reciba esos datos.
        No toca el core, solo envuelve las funciones utilitarias.
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
                        session_obj = getattr(request, "session", {}) or {}
                        session_details = session_obj.get("llavemx_details") or {}
                        if session_details:
                            context["pipeline_user_details"] = session_details
                            # set currentProvider if missing
                            context.setdefault("currentProvider", "llavemx")
                    return context
                return wrapper

            auth_utils.get_auth_context = _with_llavemx_fallback(auth_utils.get_auth_context)
            auth_utils.get_mfe_context = _with_llavemx_fallback(auth_utils.get_mfe_context)

            logger.info("[LlaveMX] Patched MFE/auth context to include llavemx_details fallback.")

        except Exception as e:
            logger.exception(f"[LlaveMX] Failed to patch MFE context: {e}")

        # Parche para exponer todos los fields en pipeline_user_details (sin serialización restrictiva)
        try:
            from openedx.core.djangoapps.user_authn.serializers import ContextDataSerializer

            def _get_pipeline_user_details_passthrough(self, obj):  # pylint: disable=unused-argument
                return obj.get("pipeline_user_details") or {}

            ContextDataSerializer.get_pipelineUserDetails = _get_pipeline_user_details_passthrough
            logger.info("[LlaveMX] Patched ContextDataSerializer to return full pipeline_user_details.")
            self._context_patched = True
        except Exception as e:
            logger.exception(f"[LlaveMX] Failed to patch serializer for pipeline_user_details: {e}")
