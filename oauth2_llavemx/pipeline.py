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
    Asociación por CURP solo para el backend LlaveMX.

    Reglas:
    - Si social-auth ya resolvió un user, reactivarlo si está inactivo y retornar.
    - Ignorar CURP genérico.
    - Asociar solo si hay exactamente un usuario activo con ese CURP.
    - Si hay múltiples activos, cancelar la asociación automática (log de error).
    """
    backend_name = getattr(backend, "name", None)

    if backend_name != "llavemx":
        return {"user": user}

    if ExtraInfo is None:
        logger.error("[LlaveMX] ExtraInfo no disponible. Se omite CURP.")
        return {"user": user}

    # Si social-auth ya resolvió el usuario, solo garantizar que esté activo
    if user is not None:
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
            logger.info("[LlaveMX] Cuenta reactivada en pipeline. user_id=%s", user.id)
        return {"user": user}

    details = details or {}
    curp = details.get("curp")

    if not curp:
        return {"user": None}

    if curp.upper() == "XEXX010101HDFXXX04":
        logger.warning("[LlaveMX] CURP genérico detectado. Asociación omitida.")
        return {"user": None}

    matches = (
        ExtraInfo.objects
        .filter(curp__iexact=curp)
        .select_related("user")
    )

    if not matches.exists():
        return {"user": None}

    users = [ei.user for ei in matches if ei.user]
    active_users = [u for u in users if u.is_active]

    if len(active_users) > 1:
        logger.error(
            "[LlaveMX] CURP con múltiples cuentas activas — asociación cancelada. "
            "curp=%s users=%s",
            curp,
            [u.id for u in active_users],
        )
        return {"user": None}

    if len(active_users) == 1:
        logger.info("[LlaveMX] Asociación por CURP exitosa. user_id=%s", active_users[0].id)
        return {"user": active_users[0]}

    if len(users) == 1:
        u = users[0]
        u.is_active = True
        u.save(update_fields=["is_active"])
        logger.info("[LlaveMX] Cuenta inactiva reactivada por asociación CURP. user_id=%s", u.id)
        return {"user": u}

    logger.warning(
        "[LlaveMX] Asociación CURP no concluyente. curp=%s total_users=%s",
        curp, len(users),
    )
    return {"user": None}


def preserve_llavemx_details(backend, details=None, *args, **kwargs):
    """
    Preserva los details de LlaveMX en sesión para que el MFE pueda accederlos.
    Solo aplica cuando el backend es LlaveMX.
    """
    if getattr(backend, "name", None) != "llavemx":
        return {}

    details = details or {}
    kwargs["details"] = details

    try:
        backend.strategy.session_set("llavemx_details", details)
    except Exception:
        logger.exception("[LlaveMX] No se pudo guardar llavemx_details en sesión.")

    return {"details": details}
