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
    Asociación por CURP SOLO para LlaveMX.
    Reglas:
    - No tocar si ya hay user
    - Ignorar CURP genérico
    - Asociar SOLO si hay exactamente UN usuario activo
    - Bloquear si hay ambigüedad
    """

    backend_name = getattr(backend, "name", None)

    # 🔐 Solo LlaveMX
    if backend_name != "llavemx":
        return {"user": user}

    # Seguridad defensiva
    if ExtraInfo is None:
        logger.error("[LlaveMX] ExtraInfo no disponible. Se omite CURP.")
        return {"user": user}

    # Si ya hay usuario, no reasociar
    if user is not None:
        return {"user": user}

    details = details or {}
    curp = details.get("curp")

    logger.warning(
        "[LlaveMX][DEBUG] associate_by_curp curp=%s",
        curp,
    )

    # Sin CURP → no asociar
    if not curp:
        return {"user": None}

    # CURP genérico → NO asociar
    if curp.upper() == "XEXX010101HDFXXX04":
        logger.warning("[LlaveMX] CURP genérico detectado. Asociación bloqueada.")
        return {"user": None}

    # Buscar coincidencias
    matches = (
        ExtraInfo.objects
        .filter(curp__iexact=curp)
        .select_related("user")
    )

    if not matches.exists():
        return {"user": None}

    # Extraer usuarios válidos
    users = [ei.user for ei in matches if ei.user]

    # Filtrar activos
    active_users = [u for u in users if u.is_active]

    # 🔴 Caso peligroso: más de una cuenta activa
    if len(active_users) > 1:
        logger.error(
            "[LlaveMX][BLOCKED] CURP duplicado con múltiples cuentas activas. "
            "Asociación automática cancelada. curp=%s users=%s",
            curp,
            [u.id for u in active_users],
        )
        return {"user": None}

    # ✅ Caso seguro: exactamente una activa
    if len(active_users) == 1:
        u = active_users[0]
        logger.warning(
            "[LlaveMX] Asociación por CURP exitosa. user_id=%s",
            u.id,
        )
        return {"user": u}

    # 🟡 Caso raro: ninguno activo, pero solo uno total
    if len(users) == 1:
        u = users[0]
        logger.warning(
            "[LlaveMX] Asociación por CURP con cuenta inactiva. user_id=%s",
            u.id,
        )
        return {"user": u}

    # Todo lo demás → no asociar
    logger.warning(
        "[LlaveMX] Asociación por CURP no concluyente. curp=%s total_users=%s",
        curp,
        len(users),
    )
    return {"user": None}


def preserve_llavemx_details(backend, details=None, *args, **kwargs):
    """
    Asegura que los datos completos de LlaveMX (details) lleguen al MFE.

    - Solo aplica cuando el backend es LlaveMX.
    - Reinyecta `details` en kwargs para que queden en el partial pipeline
      y sean expuestos como `pipeline_user_details` en el endpoint de TPA.
    - Además los persiste en sesión (llavemx_details) como fallback para el MFE.
    """
    backend_name = getattr(backend, "name", None)
    if backend_name != "llavemx":
        return {}

    # Garantizamos que details no sea None y se mantenga intacto
    details = details or {}
    kwargs["details"] = details

    # Persistir en sesión como respaldo para MFE
    try:
        backend.strategy.session_set("llavemx_details", details)
    except Exception:
        logger.exception("[LlaveMX] No se pudo guardar llavemx_details en sesión.")

    return {"details": details}
