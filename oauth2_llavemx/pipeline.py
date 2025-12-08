import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from social_django.models import UserSocialAuth

# ExtraInfo es opcional por si en algún contexto no está migrado
try:
    from custom_reg_form.models import ExtraInfo
except Exception:  # pragma: no cover
    ExtraInfo = None

User = get_user_model()

__all__ = ["associate_by_curp"]

logger = logging.getLogger(__name__)


def associate_by_curp(strategy, backend, uid, details, user=None, *args, **kwargs):
    """
    Asociación automática de cuentas para LlaveMX basada en CURP (y como fallback email).

    Reglas:
    - Si ya hay un UserSocialAuth → login normal.
    - Si existe un usuario con ese CURP en ExtraInfo → asociar.
    - Si coincide el email → asociar.
    - Si no existe → dejar que Open edX cree el usuario normalmente.
    """

    logger.info(
        "CURP_PIPELINE: start backend=%s uid=%s user=%s",
        getattr(backend, "name", None),
        uid,
        getattr(user, "id", None),
    )

    # Solo nos interesa para el backend LlaveMX
    if getattr(backend, "name", None) != "llavemx":
        logger.info("CURP_PIPELINE: backend != 'llavemx', saliendo.")
        return {}

    # Si ya viene user en el contexto, no hacemos nada raro
    if user:
        logger.info(
            "CURP_PIPELINE: user ya presente en kwargs. user_id=%s, regresando tal cual.",
            user.id,
        )
        return {"user": user}

    provider = backend.name
    uid_str = str(uid)
    curp = (details.get("curp") or "").strip()
    email = (details.get("email") or "").strip()

    logger.info(
        "CURP_PIPELINE: detalles recibidos. curp=%s email=%s", curp, email
    )

    # 1) ¿Ya existe algún social auth con este provider+uid?
    existing_social = UserSocialAuth.objects.filter(
        provider=provider, uid=uid_str
    ).first()
    if existing_social:
        logger.info(
            "CURP_PIPELINE: ya existe UserSocialAuth. provider=%s uid=%s user_id=%s",
            provider,
            uid_str,
            existing_social.user_id,
        )
        return {"user": existing_social.user}

    # 2) Buscar por CURP en ExtraInfo (tu tabla custom)
    if curp:
        logger.info("CURP_PIPELINE: buscando ExtraInfo por curp=%s", curp)

        if ExtraInfo is not None:
            try:
                extra = (
                    ExtraInfo.objects.select_related("user")
                    .get(curp__iexact=curp)
                )
                logger.info(
                    "CURP_PIPELINE: encontrado ExtraInfo id=%s user_id=%s",
                    extra.id,
                    getattr(extra, "user_id", None),
                )

                if getattr(extra, "user_id", None):
                    user_obj = extra.user
                    UserSocialAuth.objects.get_or_create(
                        user=user_obj, provider=provider, uid=uid_str
                    )
                    logger.info(
                        "CURP_PIPELINE: asociado por ExtraInfo.curp. user_id=%s",
                        user_obj.id,
                    )
                    return {"user": user_obj}
                else:
                    logger.warning(
                        "CURP_PIPELINE: ExtraInfo tiene curp pero no tiene user asociado. id=%s",
                        extra.id,
                    )

            except ExtraInfo.DoesNotExist:
                logger.info(
                    "CURP_PIPELINE: NO se encontró ExtraInfo con curp=%s", curp
                )
            except MultipleObjectsReturned:
                logger.warning(
                    "CURP_PIPELINE: múltiples ExtraInfo con curp=%s. No se asocia.",
                    curp,
                )
        else:
            logger.warning(
                "CURP_PIPELINE: ExtraInfo no está disponible (import falló)."
            )

        # 3) (Opcional) Si también tuvieras profile.curp en UserProfile
        try:
            curp_user = User.objects.select_related().get(
                profile__curp__iexact=curp
            )
            logger.info(
                "CURP_PIPELINE: encontrado UserProfile con curp. user_id=%s",
                curp_user.id,
            )
            UserSocialAuth.objects.get_or_create(
                user=curp_user, provider=provider, uid=uid_str
            )
            return {"user": curp_user}
        except User.DoesNotExist:
            logger.info(
                "CURP_PIPELINE: no hay User con profile.curp=%s (esto puede ser normal).",
                curp,
            )
        except MultipleObjectsReturned:
            logger.warning(
                "CURP_PIPELINE: múltiples Users con profile.curp=%s. No se asocia.",
                curp,
            )

    # 4) Fallback: buscar por email
    if email:
        logger.info("CURP_PIPELINE: buscando User por email=%s", email)
        email_user = User.objects.filter(email__iexact=email).first()
        if email_user:
            logger.info(
                "CURP_PIPELINE: encontrado User por email. user_id=%s",
                email_user.id,
            )
            UserSocialAuth.objects.get_or_create(
                user=email_user, provider=provider, uid=uid_str
            )
            return {"user": email_user}
        else:
            logger.info(
                "CURP_PIPELINE: no se encontró User con email=%s", email
            )

    logger.info(
        "CURP_PIPELINE: no se encontró usuario por curp ni email. "
        "Se permite que continúe create_user."
    )
    return {}
