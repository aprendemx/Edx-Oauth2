from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from social_django.models import UserSocialAuth

User = get_user_model()
__all__ = ["associate_by_curp"]


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
        return {"user": user}

    provider = backend.name
    uid_str = str(uid)
    curp = (details.get("curp") or "").strip()
    email = (details.get("email") or "").strip()

    existing_social = UserSocialAuth.objects.filter(provider=provider, uid=uid_str).first()
    if existing_social:
        return {"user": existing_social.user}

    if curp:
        try:
            curp_user = User.objects.select_related("profile").get(profile__curp__iexact=curp)
        except User.DoesNotExist:
            curp_user = None
        except MultipleObjectsReturned:
            return {}

        if curp_user:
            UserSocialAuth.objects.get_or_create(user=curp_user, provider=provider, uid=uid_str)
            return {"user": curp_user}

    if email:
        email_user = User.objects.filter(email=email).first()
        if email_user:
            UserSocialAuth.objects.get_or_create(user=email_user, provider=provider, uid=uid_str)
            return {"user": email_user}

    return {}
