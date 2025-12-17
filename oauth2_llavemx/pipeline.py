import logging

from django.contrib.auth import get_user_model
from social_core.exceptions import AuthForbidden

try:
    from custom_reg_form.models import ExtraInfo
except Exception:
    ExtraInfo = None

# 👇 MODELO OPERATIVO (vive en users)
try:
    from users.models import LlaveMXBlockedLogin
except Exception:
    LlaveMXBlockedLogin = None


logger = logging.getLogger(__name__)
User = get_user_model()


def associate_by_curp(backend, details, user=None, *args, **kwargs):
    """
    Asociación por CURP SOLO para LlaveMX.

    Reglas:
    - Si social-auth ya resolvió un user → NO tocar
    - Ignorar CURP genérico
    - Asociar SOLO si hay exactamente UN usuario activo
    - BLOQUEAR login si hay más de una cuenta activa
    """

    backend_name = getattr(backend, "name", None)

    # 🔐 Solo LlaveMX
    if backend_name != "llavemx":
        return {"user": user}

    # Seguridad defensiva
    if ExtraInfo is None:
        logger.error("[LlaveMX] ExtraInfo no disponible.")
        return {"user": user}

    # Si ya hay usuario resuelto por social-auth, no reasociar
    if user is not None:
        return {"user": user}

    details = details or {}

    # 📌 Datos LlaveMX
    curp = details.get("curp")
    uid = (
        details.get("idUsuario")  # recomendado (manual LlaveMX)
        or details.get("uid")
        or details.get("sub")
    )
    email = details.get("email") or details.get("correo")

    logger.warning(
        "[LlaveMX][DEBUG] Login attempt curp=%s uid=%s",
        curp,
        uid,
    )

    # Sin CURP → permitir flujo normal (casos raros)
    if not curp:
        return {"user": None}

    # CURP genérico → no asociar
    if curp.upper() == "XEXX010101HDFXXX04":
        logger.warning("[LlaveMX] CURP genérico detectado.")
        return {"user": None}

    # 🔍 Buscar usuarios por CURP
    matches = (
        ExtraInfo.objects
        .filter(curp__iexact=curp)
        .select_related("user")
    )

    if not matches.exists():
        return {"user": None}

    users = [ei.user for ei in matches if ei.user]
    active_users = [u for u in users if u.is_active]

    # 🔴 MULTICUENTA → BLOQUEO DURO
    if len(active_users) > 1:
        logger.error(
            "[LlaveMX][BLOCKED] CURP duplicado con múltiples cuentas activas. "
            "curp=%s users=%s",
            curp,
            [u.id for u in active_users],
        )

        # 🗂️ Registrar caso para SisAdmin
        if LlaveMXBlockedLogin and uid:
            try:
                LlaveMXBlockedLogin.objects.update_or_create(
                    uid=str(uid),
                    defaults={
                        "curp": curp,
                        "email": email,
                        "resolved": False,
                        "resolved_at": None,
                        "resolved_by": None,
                        "selected_user": None,
                    },
                )
            except Exception:
                logger.exception("[LlaveMX] Error guardando LlaveMXBlockedLogin")

        # ⛔ Detener pipeline (NO crear auth_user ni social_auth)
        raise AuthForbidden(
            backend,
            "CURP_DUPLICADO_CONTACTE_SOPORTE"
        )

    # ✅ Caso ideal: una sola cuenta activa
    if len(active_users) == 1:
        u = active_users[0]
        logger.info(
            "[LlaveMX] Asociación por CURP exitosa user_id=%s",
            u.id,
        )
        return {"user": u}

    # 🟡 Caso raro: una sola cuenta total (inactiva)
    if len(users) == 1:
        u = users[0]
        logger.info(
            "[LlaveMX] Asociación por CURP con cuenta inactiva user_id=%s",
            u.id,
        )
        return {"user": u}

    # Todo lo demás → no asociar
    logger.warning(
        "[LlaveMX] Asociación no concluyente curp=%s total_users=%s",
        curp,
        len(users),
    )
    return {"user": None}


def preserve_llavemx_details(backend, details=None, *args, **kwargs):
    """
    Preserva los details de LlaveMX para el MFE.
    """

    backend_name = getattr(backend, "name", None)
    if backend_name != "llavemx":
        return {}

    details = details or {}
    kwargs["details"] = details

    try:
        backend.strategy.session_set("llavemx_details", details)
    except Exception:
        logger.exception("[LlaveMX] No se pudo guardar llavemx_details en sesión")

    return {"details": details}
