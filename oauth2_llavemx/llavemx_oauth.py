"""
Llave MX OAuth2 Backend (API WEB)
Integración oficial con Open edX mediante Python Social Auth.

Esta implementación sigue al 100% el Manual Técnico de Llave MX (modo Web),
usando los endpoints /oauth/ y autenticación BasicAuth en los servicios
obtenidos desde usuario_ws y password_ws.

Características:
- OAuth2 Authorization Code (sin PKCE, Web NO lo usa)
- BasicAuth en todos los servicios protegidos
- Campos mapeados para MéxicoX / EMI / MFE
- Seguro, limpio y auditable
"""

import json
import base64
import logging
from urllib.request import Request, urlopen

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed, AuthUnknownError
from django.conf import settings

logger = logging.getLogger(__name__)
VERBOSE = True


class LlaveMXOAuth2(BaseOAuth2):
    """
    Backend OAuth2 de LlaveMX modo Web.

    * No usa PKCE
    * Usa client_secret obligatorio
    * Usa BasicAuth (usuario_ws + password_ws)
    * Devuelve accessToken y refreshToken
    * Expira en milisegundos → se convierte a segundos
    """

    name = "llavemx"
    REDIRECT_STATE = True
    ACCESS_TOKEN_METHOD = "POST"
    DEFAULT_SCOPE = []
    REQUIRES_EMAIL_VALIDATION = False

    # ENDPOINTS WEB (no Apps)
    AUTHORIZATION_URL = "https://val-llavemx.infotec.mx/oauth.xhtml"
    ACCESS_TOKEN_URL = "https://val-api-llavemx.infotec.mx/ws/rest/oauth/obtenerToken"
    USER_DATA_URL = "https://val-api-llavemx.infotec.mx/ws/rest/oauth/datosUsuario"
    ROLES_URL = "https://val-api-llavemx.infotec.mx/ws/rest/oauth/getRolesUsuarioLogueado"
    LOGOUT_URL = "https://val-api-llavemx.infotec.mx/ws/rest/oauth/cerrarSesion"

    # Campos guardados en UserSocialAuth.extra_data
    EXTRA_DATA = [
        ("id", "id"),
        ("curp", "curp"),
        ("telefono", "telefono"),
        ("fechaNacimiento", "fechaNacimiento"),
        ("sexo", "sexo"),
        ("correoVerificado", "correoVerificado"),
        ("telefonoVerificado", "telefonoVerificado"),
        ("refresh_token", "refresh_token"),
    ]

    UPDATE_USER_ON_LOGIN = True

    # =============================================================
    # HELPERS
    # =============================================================

    def _basic_auth(self):
        """Construye el header Basic Auth requerido por LlaveMX Web."""
        user = settings.SOCIAL_AUTH_LLAVEMX_WS_USER
        pwd = settings.SOCIAL_AUTH_LLAVEMX_WS_PASSWORD

        if not user or not pwd:
            raise AuthFailed(self, "Faltan credenciales WS (usuario_ws o password_ws).")

        raw = f"{user}:{pwd}".encode("utf-8")
        encoded = base64.b64encode(raw).decode("utf-8")
        return f"Basic {encoded}"

    # =============================================================
    # TOKEN EXCHANGE (Authorization Code)
    # =============================================================

    def request_access_token(self, *args, **kwargs):
        code = self.data.get("code")
        if not code:
            raise AuthFailed(self, "No se recibió parámetro 'code'.")

        client_id = self.setting("KEY")
        client_secret = self.setting("SECRET")
        redirect_uri = self.get_redirect_uri()

        payload = {
            "grantType": "authorization_code",
            "code": code,
            "redirectUri": redirect_uri,
            "clientId": client_id,
            "clientSecret": client_secret,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth(),
            "Accept": "application/json",
        }

        try:
            req = Request(
                self.ACCESS_TOKEN_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            resp = urlopen(req)
            data = json.loads(resp.read().decode("utf-8"))

            access_token = data.get("accessToken")
            if not access_token:
                raise AuthFailed(self, "LlaveMX no retornó accessToken.")

            expires_raw = data.get("expiresIn", 900)
            expires_in = int(expires_raw / 1000) if expires_raw > 10_000_000 else expires_raw

            return {
                "access_token": access_token,
                "expires_in": expires_in,
                "refresh_token": data.get("refreshToken"),
                "token_type": "Bearer",
            }

        except Exception as e:
            logger.error(f"LlaveMX token error: {e}")
            raise AuthUnknownError(self, str(e))

    # =============================================================
    # USER DATA
    # =============================================================

    def user_data(self, access_token, *args, **kwargs):
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth(),
            "accessToken": access_token,
        }

        try:
            req = Request(self.USER_DATA_URL, headers=headers, method="GET")
            resp = urlopen(req)
            data = json.loads(resp.read().decode("utf-8"))

            if not self._valid_user_response(data):
                raise AuthFailed(self, "Respuesta inválida de LlaveMX.")

            return data

        except Exception as e:
            logger.error(f"LlaveMX user_data error: {e}")
            raise AuthUnknownError(self, str(e))

    def _valid_user_response(self, data):
        if not isinstance(data, dict):
            return False
        if "idUsuario" not in data:
            return False
        if not (data.get("correo") or data.get("login") or data.get("telVigente")):
            return False
        return True

    # =============================================================
    # USER ID
    # =============================================================

    def get_user_id(self, details, response):
        return str(response.get("idUsuario") or details.get("username"))

    # =============================================================
    # USER DETAILS MAPPING
    # =============================================================

    def get_user_details(self, response):
        curp = (response.get("curp") or "").strip()
        login = (response.get("login") or "").strip()
        username = curp if curp else login

        email = (response.get("correo") or "").strip()
        if not email and login:
            email = f"{login}@llavemx.temp"

        nombres = (response.get("nombre") or "").strip()
        primer_ap = (response.get("primerApellido") or "").strip()
        segundo_ap = (response.get("segundoApellido") or "").strip()

        full_name = " ".join(filter(None, [nombres, primer_ap, segundo_ap]))
        last_name = " ".join(filter(None, [primer_ap, segundo_ap]))

        return {
            "id": response.get("idUsuario", ""),
            "username": username,
            "email": email,
            "name": full_name,
            "first_name": nombres,
            "last_name": last_name,

            # Datos personalizados MéxicoX
            "nombres": nombres,
            "primer_apellido": primer_ap,
            "segundo_apellido": segundo_ap,
            "curp": curp,
            "telefono": response.get("telVigente") or response.get("telefono") or "",
            "fechaNacimiento": response.get("fechaNacimiento") or "",
            "sexo": response.get("sexo") or "",
            "correoVerificado": bool(response.get("correoVerificado", False)),
            "telefonoVerificado": bool(response.get("telefonoVerificado", False)),
            "estado": response.get("estadoNacimiento") or "",
            "municipio": (response.get("domicilio") or {}).get("alcaldiaMunicipio", ""),

            # Campos que el MFE espera
            "pais": "",
            "dni": "",
            "ocupacion": "",
            "maximo_nivel": "",
            "eres_docente": False,
            "cct": "",
            "funcion": "",
            "nivel_Educativo": "",
            "asignatura": "",
            "cuentanos": "",
        }
