"""
Llave MX OAuth2 Backend (API WEB)
Integración oficial con Open edX mediante Python Social Auth.

Esta implementación sigue el Manual Técnico LlaveMX (Aplicación Web):
- OAuth2 Authorization Code sin PKCE
- Se usa client_secret obligatorio
- Todas las llamadas autenticadas usan BasicAuth (usuario_ws + password_ws)
- Se consumen los endpoints Web: /ws/rest/oauth/*

NOTAS DE SEGURIDAD IMPLEMENTADAS:

1) Parámetro "state" contra CSRF (Manual LlaveMX, sección 3.2)
   - Valor criptográficamente seguro y único por solicitud
   - Se guarda en sesión
   - Se valida al recibir el callback

2) Intercambio de "code" por "token" SOLO desde backend (3.5)
   - Se hace desde el servidor usando BasicAuth y client_secret
   - Se maneja el escenario de "code" inválido/expirado

3) Manejo seguro de token de acceso (4.1)
   - No se expone al frontend
   - Se valida respuesta y error "invalid_token"

4) Cierre de sesión remoto LlaveMX (5.1)
   - Se implementa revoke_token() que llama al WS /cerrarSesion
   - Se usa BasicAuth + accessToken en header
   - Se envía body "{}" para evitar HTTP 411 en productivo
"""

import json
import base64
import logging
import secrets
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed, AuthUnknownError
from django.conf import settings

logger = logging.getLogger(__name__)
VERBOSE = True


class LlaveMXOAuth2(BaseOAuth2):

    name = "llavemx"
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = "POST"
    DEFAULT_SCOPE = []
    REQUIRES_EMAIL_VALIDATION = False

    # Endpoints Web
    AUTHORIZATION_URL = "https://www.llave.gob.mx/oauth.xhtml"
    ACCESS_TOKEN_URL  = "https://api.llave.gob.mx/ws/rest/oauth/obtenerToken"
    USER_DATA_URL     = "https://api.llave.gob.mx/ws/rest/oauth/datosUsuario"
    ROLES_URL         = "https://api.llave.gob.mx/ws/rest/oauth/getRolesUsuarioLogueado"
    LOGOUT_URL        = "https://api.llave.gob.mx/ws/rest/oauth/cerrarSesion"

    # NOTA DE SEGURIDAD:
    # Guardamos también el access_token para poder consumir /cerrarSesion
    EXTRA_DATA = [
        ("id", "id"),
        ("curp", "curp"),
        ("telefono", "telefono"),
        ("fechaNacimiento", "fechaNacimiento"),
        ("sexo", "sexo"),
        ("correoVerificado", "correoVerificado"),
        ("telefonoVerificado", "telefonoVerificado"),
        ("refresh_token", "refresh_token"),
        ("access_token", "access_token"),
    ]

    UPDATE_USER_ON_LOGIN = True

    # =============================================================
    # STATE MANUAL (Seguridad CSRF)
    # =============================================================
    def generate_state(self):
        """Genera un state seguro para prevenir CSRF."""
        return secrets.token_urlsafe(32)

    def auth_url(self):
        """
        Construye el URL de autorización incluyendo el parámetro STATE
        generado manualmente según las notas de seguridad de LlaveMX.
        """
        state = self.generate_state()

        self.strategy.session_set("llavemx_state", state)

        params = {
            "client_id": self.setting("KEY"),
            "redirect_url": self.get_redirect_uri(),
            "response_type": "code",
            "state": state,
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def validate_state(self):
        """
        Valida que el state del callback coincida con el generado.
        Protege contra ataques CSRF.
        """
        sent_state = self.data.get("state")
        saved_state = self.strategy.session_get("llavemx_state")

        if not sent_state or not saved_state or sent_state != saved_state:
            raise AuthFailed(self, "State inválido o inexistente. Posible CSRF.")

    def auth_complete(self, *args, **kwargs):
        """
        Validación del state antes de continuar con el flujo OAuth.
        NOTA DE SEGURIDAD:
        - LlaveMX ya valida internamente el redirect_url registrado.
        """
        self.validate_state()
        return super().auth_complete(*args, **kwargs)

    # =============================================================
    # BASIC AUTH (usuario_ws + password_ws)
    # =============================================================
    def _basic_auth(self):
        user = settings.SOCIAL_AUTH_LLAVEMX_WS_USER
        pwd = settings.SOCIAL_AUTH_LLAVEMX_WS_PASSWORD

        if not user or not pwd:
            raise AuthFailed(
                self,
                "Faltan credenciales WS (usuario_ws o password_ws)."
            )

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

        redirect_uri = self.get_redirect_uri()

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self._basic_auth(),
            "Accept": "application/json",
        }

        try:
            req = Request(
                self.ACCESS_TOKEN_URL,
                data=urlencode(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            resp = urlopen(req)
            raw = resp.read().decode("utf-8") or "{}"
            data = json.loads(raw)

            if data.get("error"):
                raise AuthFailed(
                    self,
                    f"Error LlaveMX token: {data.get('error')} - {data.get('errorDescription')}"
                )

            access_token = data.get("accessToken")
            if not access_token:
                raise AuthFailed(self, "LlaveMX no retornó accessToken.")

            return {
                "access_token": access_token,
                "expires_in": data.get("expiresIn", 900),
                "refresh_token": data.get("refreshToken"),
                "token_type": "Bearer",
            }

        except HTTPError as e:
            body = e.read().decode("utf-8")
            logger.error(f"LlaveMX token HTTPError {e.code}: {body}")
            raise AuthFailed(self, f"LlaveMX token HTTPError ({e.code})")

    # =============================================================
    # USER DATA
    # =============================================================
    def user_data(self, access_token, *args, **kwargs):
        """
        Obtiene los datos del usuario desde LlaveMX usando el accessToken.

        NOTA DE SEGURIDAD:
        - El token se envía SOLO por header desde backend.
        - No se expone el token ni la respuesta completa en el frontend.
        - Si LlaveMX responde 'invalid_token', se fuerza reautenticación.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth(),
            "accessToken": access_token,
        }

        try:
            req = Request(self.USER_DATA_URL, headers=headers, method="GET")
            resp = urlopen(req)
            raw = resp.read().decode("utf-8") or "{}"
            data = json.loads(raw)

            # Manejo explícito de invalid_token
            if isinstance(data, dict) and data.get("error"):
                error = data.get("error")
                description = data.get("errorDescription") or data.get("error_description") or ""
                msg = f"Error al obtener datos de usuario LlaveMX: {error} - {description}"

                if error == "invalid_token":
                    # NOTA DE SEGURIDAD:
                    # No damos acceso, obligamos a reiniciar el flujo de autenticación.
                    raise AuthFailed(self, msg)

                raise AuthUnknownError(self, msg)

            if not self._valid_user_response(data):
                raise AuthFailed(self, "Respuesta inválida de LlaveMX al obtener datos de usuario.")

            return data

        except HTTPError as e:
            try:
                body = e.read().decode("utf-8") or "{}"
                data = json.loads(body)
            except Exception:
                data = {}
            error = data.get("error") or e.reason
            description = data.get("errorDescription") or data.get("error_description") or ""
            msg = f"LlaveMX user_data HTTPError ({e.code}): {error} - {description}"
            logger.error(msg)
            raise AuthFailed(self, msg)
        except (URLError, ValueError) as e:
            logger.error(f"LlaveMX user_data error de red/parsing: {e}")
            raise AuthUnknownError(self, str(e))
        except AuthFailed:
            raise
        except Exception as e:
            logger.error(f"LlaveMX user_data error inesperado: {e}")
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

    # =============================================================
    # LOGOUT / REVOCACIÓN DE TOKEN
    # =============================================================
    def revoke_token(self, token, response=None, *args, **kwargs):
        """
        Cierra la sesión de la cuenta LlaveMX consumiendo el WS /cerrarSesion.

        NOTA DE SEGURIDAD (Manual 5.1):
        - Se usa BasicAuth (usuario_ws + password_ws).
        - Se envía accessToken en header.
        - Se envía body "{}" para evitar HTTP 411 en productivo.
        """
        if not token:
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth(),
            "accessToken": token,
        }

        try:
            req = Request(
                self.LOGOUT_URL,
                data="{}".encode("utf-8"),  # workaround HTTP 411 Length Required
                headers=headers,
                method="POST",
            )
            resp = urlopen(req)
            raw = resp.read().decode("utf-8") or "{}"
            data = json.loads(raw)
            if VERBOSE:
                logger.info(f"LlaveMX logout response: {data}")
        except Exception as e:
            logger.error(f"LlaveMX logout error: {e}")
            # No rompemos el logout de Open edX aunque falle el WS remoto.
            return
