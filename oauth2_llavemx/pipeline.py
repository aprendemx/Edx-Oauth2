import logging

from django.contrib.auth import get_user_model
from custom_reg_form.models import ExtraInfo

logger = logging.getLogger(__name__)
User = get_user_model()


def associate_by_curp(backend, details, user=None, *args, **kwargs):
    """
    Paso de pipeline para asociar por CURP.

    DEBUG:
    - Siempre logea cuando entra.
    - No filtramos por backend.name para ver si realmente se ejecuta.
    """

    backend_name = getattr(backend, "name", None)
    curp = (details or {}).get("curp")
    email = (details or {}).get("email")

    logger.warning(
        "[LlaveMX][DEBUG] associate_by_curp llamado. backend=%s curp=%s email=%s user=%s",
        backend_name,
        curp,
        email,
        getattr(user, "id", None),
    )

    # Si ya hay usuario, no hacemos nada (ya lo encontró otro paso)
    if user is not None:
        logger.warning(
            "[LlaveMX][DEBUG] Ya viene user en el pipeline (id=%s). No reasociamos.",
            user.id,
        )
        return {"user": user}

    if not curp:
        logger.warning("[LlaveMX][DEBUG] No hay CURP en details. No se asocia.")
        return {}

    # Buscar ExtraInfo por CURP (ignorando mayúsculas/minúsculas)
    matches = ExtraInfo.objects.filter(curp__iexact=curp).select_related("user")

    if not matches.exists():
        logger.warning(
            "[LlaveMX][DEBUG] No se encontró ExtraInfo para CURP=%s", curp
        )
        return {}

    extra = matches.first()
    user = extra.user

    logger.warning(
        "[LlaveMX][DEBUG] ExtraInfo encontrado. Asociando user.id=%s username=%s email=%s",
        user.id,
        user.username,
        user.email,
    )

    # Devolvemos el usuario para que el pipeline continúe ya asociado
    return {"user": user}
