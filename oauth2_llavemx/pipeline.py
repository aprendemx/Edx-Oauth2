import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from social_django.models import UserSocialAuth

from custom_reg_form.models import ExtraInfo

User = get_user_model()
__all__ = ["associate_by_curp"]

logger = logging.getLogger(__name__)


def associate_by_curp(strategy, backend, uid, details, user=None, *args, **kwargs):
    """
    Asociación automática de cuentas para LlaveMX basada en CURP.

    Reglas:
    - Si ya hay un UserSocialAuth → login normal.
    - Si existe un usuario con ese CURP en el perfil → asociar.
    - Si coincide el email → asociar.
    - Si no existe → dejar que Open edX cree el usuario normalmente.
    """

    if backend.name != "llavemx":
        return {}

    if user:
        logger.info("associate_by_curp: user already present, skipping. user_id=%s", user.id)
        return {"user": user}

    provider = backend.name
    uid_str = str(uid)
    curp = (details.get("curp") or "").strip()
    email = (details.get("email") or "").strip()

    existing_social = UserSocialAuth.objects.filter(provider=provider, uid=uid_str).first()
    if existing_social:
        logger.info("associate_by_curp: found existing social auth for uid=%s user_id=%s", uid_str, existing_social.user_id)
        return {"user": existing_social.user}

    if curp:
        extra_user = ExtraInfo.objects.filter(curp__iexact=curp.strip()).select_related("user").first()
        if extra_user:
            user_obj = extra_user.user
            UserSocialAuth.objects.get_or_create(user=user_obj, provider=provider, uid=uid_str)
            logger.info("associate_by_curp: matched ExtraInfo curp=%s user_id=%s", curp, user_obj.id)
            return {"user": user_obj}

        try:
            curp_user = User.objects.select_related("profile").get(profile__curp__iexact=curp)
        except User.DoesNotExist:
            curp_user = None
        except MultipleObjectsReturned:
            logger.warning("associate_by_curp: multiple users with curp=%s, no association", curp)
            return {}

        if curp_user:
            UserSocialAuth.objects.get_or_create(user=curp_user, provider=provider, uid=uid_str)
            logger.info("associate_by_curp: matched profile curp=%s user_id=%s", curp, curp_user.id)
            return {"user": curp_user}

    if email:
        email_user = User.objects.filter(email=email).first()
        if email_user:
            UserSocialAuth.objects.get_or_create(user=email_user, provider=provider, uid=uid_str)
            logger.info("associate_by_curp: matched email=%s user_id=%s", email, email_user.id)
            return {"user": email_user}

    logger.info("associate_by_curp: no match for curp=%s email=%s uid=%s", curp, email, uid_str)
    return {}
