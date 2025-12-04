# oauth2_llavemx/pipeline.py
from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def associate_by_curp(strategy, backend, uid, details, user=None, *args, **kwargs):
    """
    Asociación automática de cuentas para LlaveMX.

    - Si el usuario YA existe en LMS → vincula
    - Si solo se encuentra por CURP → vincula
    - Si no existe → dejar que pipeline normal lo cree
    """

    if backend.name != "llavemx":
        return

    # Si ya hay usuario autenticado, no hacer nada
    if user:
        return {"user": user}

    curp = details.get("curp") or details.get("CURP") or ""
    email = details.get("email") or ""
    provider = backend.name
    uid_str = str(uid)

    # ------------------------------------------
    # 1) Si ya existe un vínculo social → login normal
    # ------------------------------------------
    try:
        existing_social = UserSocialAuth.objects.get(provider=provider, uid=uid_str)
        return {"user": existing_social.user}
    except UserSocialAuth.DoesNotExist:
        pass

    # ------------------------------------------
    # 2) Buscar por CURP (preferido)
    # ------------------------------------------
    if curp:
        try:
            existing_by_curp = User.objects.get(profile__curp=curp)
            with transaction.atomic():
                UserSocialAuth.objects.create(
                    user=existing_by_curp,
                    provider=provider,
                    uid=uid_str,
                )
            return {"user": existing_by_curp}
        except User.DoesNotExist:
            pass

    # ------------------------------------------
    # 3) Buscar por email
    # ------------------------------------------
    if email:
        try:
            existing_by_email = User.objects.get(email=email)
            with transaction.atomic():
                UserSocialAuth.objects.create(
                    user=existing_by_email,
                    provider=provider,
                    uid=uid_str,
                )
            return {"user": existing_by_email}
        except User.DoesNotExist:
            pass

    # ------------------------------------------
    # 4) No existe → que las fases siguientes creen usuario
    # ------------------------------------------
    return None
