from django.contrib.auth import get_user_model
from registration_form.models import ExtraInfo  # tu modelo real
from social_core.exceptions import AuthFailed

User = get_user_model()

def associate_by_curp(strategy, details, backend, user=None, *args, **kwargs):
    """
    Intenta enlazar automáticamente una cuenta local usando el CURP
    recibido desde LlaveMX.

    Esto funciona cuando el usuario YA EXISTE pero no había
    enlazado su cuenta con LlaveMX anteriormente.
    """

    # Solo se ejecuta para LlaveMX
    if backend.name != "llavemx":
        return

    # Si PSA ya encontró usuario asociado → no hacemos nada
    if user:
        return {"is_new": False, "user": user}

    curp = details.get("curp")

    if not curp or curp.strip() == "":
        # LlaveMX no regresó CURP → no podemos enlazar
        return

    try:
        extra = ExtraInfo.objects.get(curp__iexact=curp.strip())
        usuario_local = extra.user

        # IMPORTANTE: regresamos user y marcamos is_new=False
        # para que NO vaya al flujo de registro
        return {
            "user": usuario_local,
            "is_new": False,
            "details": details,
        }

    except ExtraInfo.DoesNotExist:
        # No existe usuario con ese CURP → sigue el pipeline normal
        return
