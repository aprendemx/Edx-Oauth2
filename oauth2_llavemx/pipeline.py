import logging

from django.contrib.auth import get_user_model

try:
    from custom_reg_form.models import ExtraInfo
except Exception:
    ExtraInfo = None

logger = logging.getLogger(__name__)
User = get_user_model()


def associate_by_curp(backend, details, user=None, *args, **kwargs):
    """
    Paso de pipeline para asociar por CURP SOLO cuando el backend es LlaveMX.
    Esto evita romper Studio (edx-oauth2) y el login normal.
    """

    backend_name = getattr(backend, "name", None)

    # 🔐 ***FILTRO CRÍTICO*** → SOLO ejecutar si el backend es LlaveMX
    if backend_name != "llavemx":
        logger.warning(
            "[LlaveMX][DEBUG] associate_by_curp ignorado. backend=%s (no es llavemx)",
            backend_name,
        )
        return {"user": user}

    # Si por alguna razón ExtraInfo no existe, no rompemos nada
    if ExtraInfo is None:
        logger.error("[LlaveMX][ERROR] ExtraInfo no está disponible. Se omite asociación por CURP.")
        return {"user": user}

    curp = (details or {}).get("curp")
    email = (details or {}).get("email")

    logger.warning(
        "[LlaveMX][DEBUG] associate_by_curp llamado. backend=%s curp=%s email=%s user=%s",
        backend_name,
        curp,
        email,
        getattr(user, "id", None),
    )

    # Si ya hay usuario, no hacemos nada
    if user is not None:
        logger.warning(
            "[LlaveMX][DEBUG] Ya viene user (id=%s). No reasociamos.",
            user.id,
        )
        return {"user": user}

    # Sin CURP no hay asociación
    if not curp:
        logger.warning("[LlaveMX][DEBUG] No hay CURP. No se asocia.")
        return {"user": None}

    # Busca ExtraInfo por CURP
    matches = ExtraInfo.objects.filter(curp__iexact=curp).select_related("user")

    if not matches.exists():
        logger.warning(
            "[LlaveMX][DEBUG] No se encontró ExtraInfo para CURP=%s",
            curp,
        )
        return {"user": None}

    extra = matches.first()
    user = extra.user

    logger.warning(
        "[LlaveMX][DEBUG] ExtraInfo encontrado. Asociando user.id=%s username=%s email=%s",
        user.id,
        user.username,
        user.email,
    )

    return {"user": user}


def preserve_llavemx_details(backend, details=None, *args, **kwargs):
    """
    Asegura que los datos completos de LlaveMX (details) lleguen al MFE.

    - Solo aplica cuando el backend es LlaveMX.
    - Reinyecta `details` en kwargs para que queden en el partial pipeline
      y sean expuestos como `pipeline_user_details` en el endpoint de TPA.
    """
    backend_name = getattr(backend, "name", None)
    if backend_name != "llavemx":
        return {}

    # Garantizamos que details no sea None y se mantenga intacto
    details = details or {}
    kwargs["details"] = details
    return {"details": details}
