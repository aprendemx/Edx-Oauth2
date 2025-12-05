from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model
from django.db import transaction

from custom_reg_form.models import ExtraInfo

User = get_user_model()
__all__ = ["associate_by_curp"]


def associate_by_curp(strategy, backend, uid, details, user=None, *args, **kwargs):
    """
    Asociación automática de cuentas para LlaveMX basada en CURP.

    Reglas:
    - Si ya hay un UserSocialAuth → login normal.
    - Si existe un usuario con ese CURP en ExtraInfo → asociar.
    - Si coincide el email → asociar.
    - Si no existe → dejar que Open edX cree el usuario normalmente.
    """

    if backend.name != "llavemx":
        return

    # Si ya hay usuario autenticado
    if user:
        return {"user": user}

    provider = backend.name
    uid_str = str(uid)

    curp = (details.get("curp") or "").strip()
    email = (details.get("email") or "").strip()

    try:
        existing_social = UserSocialAuth.objects.get(provider=provider, uid=uid_str)
        return {"user": existing_social.user}
    except UserSocialAuth.DoesNotExist:
        pass

    if curp:
        try:
            extra = ExtraInfo.objects.get(curp=curp)
            user_obj = extra.user  # relación OneToOne
            with transaction.atomic():
                UserSocialAuth.objects.create(
                    user=user_obj,
                    provider=provider,
                    uid=uid_str,
                )
            return {"user": user_obj}
        except ExtraInfo.DoesNotExist:
            pass

    if email:
        try:
            existing_user = User.objects.get(email=email)
            with transaction.atomic():
                UserSocialAuth.objects.create(
                    user=existing_user,
                    provider=provider,
                    uid=uid_str,
                )
            return {"user": existing_user}
        except User.DoesNotExist:
            pass

    return None
