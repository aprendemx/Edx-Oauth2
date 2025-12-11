import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class OAuth2LlaveMXConfig(AppConfig):
    name = "oauth2_llavemx"
    verbose_name = "OAuth2 LlaveMX Integration"

    def ready(self):
        """
        Inserts associate_by_curp into the SOCIAL_AUTH_PIPELINE.
        We rely on the fact that TPA's settings are applied early, 
        so we modify the settings.SOCIAL_AUTH_PIPELINE list directly.
        """
        try:
            self._inject_pipeline_step()
        except Exception:
            logger.exception("[LlaveMX] Error during pipeline injection")

    def _inject_pipeline_step(self):
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

        except Exception as e:
            logger.error(f"[LlaveMX] Failed to patch SOCIAL_AUTH_PIPELINE: {e}")
