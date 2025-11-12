"""
written by:     AprendeMX Team
                OAuth2 + PKCE backend for Llave MX (Mexican Government Digital Identity)

date:           nov-2025

usage:          OAuth2 backend for Llave MX integration with Open edX.
                Handles authentication with PKCE, custom JSON POST for tokens,
                and field mapping between Llave MX and Open edX user models.

documentation:  https://www.gob.mx/llavemx
                Llave MX is the official digital identity platform of the
                Mexican Government for authenticating users in government services.
"""
from datetime import datetime
import json
import hashlib
import base64
import secrets
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from logging import getLogger
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed, AuthCanceled, AuthUnknownError


logger = getLogger(__name__)

VERBOSE_LOGGING = True


class LlaveMXOAuth2(BaseOAuth2):
    """
    Llave MX OAuth2 authentication backend for Open edX.
    
    Llave MX is the Mexican Government's unified digital identity system.
    It provides secure authentication with CURP validation, verified email,
    and phone number verification.
    
    This backend implements:
    - OAuth 2.0 + PKCE (Proof Key for Code Exchange)
    - Custom JSON POST for token exchange (non-standard)
    - User data mapping from Llave MX to Open edX format
    - Comprehensive error handling and logging
    - Optional role management integration
    
    Key differences from standard OAuth2:
    - Token endpoint requires POST with JSON body (not form-encoded)
    - Uses 'accessToken' header instead of 'Authorization: Bearer'
    - CURP is used as username (not email)
    - Custom field mapping for Mexican government data
    """

    _user_details = None
    _code_verifier = None

    # Backend identifier for Python Social Auth
    # This appears in Django Admin and URLs: /login/llavemx and /complete/llavemx
    name = "llavemx"

    # Llave MX endpoints (VAL environment - validation/testing)
    # Production URLs would use https://llave.infotec.mx instead of val-llave
    AUTHORIZATION_URL = "https://val-llave.infotec.mx/oauth.xhtml"
    ACCESS_TOKEN_URL = "https://val-api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken"
    USER_DATA_URL = "https://val-api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario"
    ROLES_URL = "https://val-api-llave.infotec.mx/ws/rest/apps/oauth/getRolesUsuarioLogueado"
    LOGOUT_URL = "https://val-api-llave.infotec.mx/ws/rest/apps/auth/cerrarSesion"

    # OAuth2 + PKCE configuration
    OAUTH_PKCE_ENABLED = True  # Force PKCE (required by Llave MX)
    REDIRECT_STATE = True      # Include state parameter for CSRF protection
    DEFAULT_SCOPE = []         # Llave MX doesn't use scopes
    
    # User identification field
    ID_KEY = "id"
    
    # Email validation not required (handled by Llave MX)
    REQUIRES_EMAIL_VALIDATION = False
    
    # Token method (we override this completely)
    ACCESS_TOKEN_METHOD = "POST"
    
    # Redirect validation
    SOCIAL_AUTH_SANITIZE_REDIRECTS = True
    
    # Extra data to store in UserSocialAuth.extra_data
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
    
    # Enable automatic user data updates on login
    UPDATE_USER_ON_LOGIN = True

    # ========================================================================
    # PKCE Implementation
    # ========================================================================
    
    def generate_code_verifier(self):
        """
        Generate a cryptographically random code verifier for PKCE.
        Must be 43-128 characters long.
        """
        if not self._code_verifier:
            self._code_verifier = base64.urlsafe_b64encode(
                secrets.token_bytes(32)
            ).decode('utf-8').rstrip('=')
        return self._code_verifier
    
    def generate_code_challenge(self, code_verifier):
        """
        Generate code challenge from verifier using S256 method.
        challenge = BASE64URL(SHA256(verifier))
        """
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        return challenge
    
    def get_code_verifier(self):
        """Retrieve stored code verifier for token exchange."""
        # Try to get from session first
        code_verifier = self.strategy.session_get('code_verifier')
        if not code_verifier:
            code_verifier = self._code_verifier
        if VERBOSE_LOGGING:
            logger.info("get_code_verifier() retrieved: {verifier}".format(
                verifier="<present>" if code_verifier else "<missing>"
            ))
        return code_verifier

    def auth_params(self, state=None):
        """
        Add PKCE parameters to authorization request.
        """
        params = super().auth_params(state)
        
        # Generate and store code verifier
        code_verifier = self.generate_code_verifier()
        self.strategy.session_set('code_verifier', code_verifier)
        
        # Add PKCE parameters
        code_challenge = self.generate_code_challenge(code_verifier)
        params['code_challenge'] = code_challenge
        params['code_challenge_method'] = 'S256'
        
        if VERBOSE_LOGGING:
            logger.info("auth_params() PKCE enabled with S256 challenge")
            logger.info("auth_params() full params: {params}".format(
                params={k: v for k, v in params.items() if k != 'code_challenge'}
            ))
        
        return params

    # ========================================================================
    # Custom Token Exchange (Llave MX uses non-standard JSON POST)
    # ========================================================================
    
    def auth_complete_params(self, state=None):
        """
        Build parameters for token request.
        Llave MX requires specific JSON structure.
        """
        client_id = self.setting('KEY')
        redirect_uri = self.get_redirect_uri(state)
        
        if VERBOSE_LOGGING:
            logger.info("auth_complete_params() client_id: {client_id}".format(
                client_id=client_id
            ))
            logger.info("auth_complete_params() redirect_uri: {uri}".format(
                uri=redirect_uri
            ))
        
        return {
            'client_id': client_id,
            'redirect_uri': redirect_uri
        }

    def request_access_token(self, *args, **kwargs):
        """
        Exchange authorization code for access token.
        
        Llave MX requires POST with JSON body (not standard form-encoded):
        {
            "grantType": "authorization_code",
            "code": "<authorization_code>",
            "redirectUri": "<callback_url>",
            "clientId": "<client_id>",
            "codeVerifier": "<pkce_verifier>"
        }
        
        Returns dict compatible with Python Social Auth:
        {
            "access_token": "...",
            "expires_in": 900,
            "refresh_token": "...",
            "token_type": "Bearer"
        }
        """
        # Get authorization code from callback
        code = self.data.get('code')
        if not code:
            error = self.data.get('error')
            error_description = self.data.get('error_description', 'No error description provided')
            logger.error("request_access_token() No code received. Error: {error}, Description: {desc}".format(
                error=error, desc=error_description
            ))
            raise AuthFailed(self, 'Authorization code not received')
        
        # Get PKCE code verifier
        code_verifier = self.get_code_verifier()
        if not code_verifier:
            logger.error("request_access_token() PKCE code_verifier not found in session")
            raise AuthFailed(self, 'PKCE code_verifier missing')
        
        # Get client credentials
        client_id = self.setting('KEY')
        redirect_uri = self.get_redirect_uri()
        
        # Build Llave MX specific JSON payload
        payload = {
            "grantType": "authorization_code",
            "code": code,
            "redirectUri": redirect_uri,
            "clientId": client_id,
            "codeVerifier": code_verifier
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if VERBOSE_LOGGING:
            logger.info("request_access_token() URL: {url}".format(url=self.ACCESS_TOKEN_URL))
            logger.info("request_access_token() payload: {payload}".format(
                payload={k: v for k, v in payload.items() if k not in ['code', 'codeVerifier']}
            ))
        
        try:
            # Make POST request with JSON body
            request = Request(
                self.ACCESS_TOKEN_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            response = urlopen(request)
            response_data = json.loads(response.read().decode('utf-8'))
            
            if VERBOSE_LOGGING:
                logger.info("request_access_token() response status: {status}".format(
                    status=response.getcode()
                ))
                # Log response without exposing full token
                safe_response = {
                    k: (v[:10] + '...' if k in ['accessToken', 'refreshToken'] and v else v)
                    for k, v in response_data.items()
                }
                logger.info("request_access_token() response: {response}".format(
                    response=json.dumps(safe_response, indent=2)
                ))
            
            # Map Llave MX response to PSA expected format
            token_response = {
                "access_token": response_data.get("accessToken"),
                "expires_in": response_data.get("expiresIn", 900),  # Default 15 min
                "refresh_token": response_data.get("refreshToken"),
                "token_type": response_data.get("tokenType", "Bearer")
            }
            
            # Validate required fields
            if not token_response.get("access_token"):
                logger.error("request_access_token() No accessToken in response")
                raise AuthFailed(self, 'No access token received from Llave MX')
            
            # Clear code verifier from session
            self.strategy.session_pop('code_verifier')
            
            return token_response
            
        except Exception as e:
            logger.error("request_access_token() Exception: {error}".format(
                error=str(e)
            ))
            
            # Check for specific Llave MX errors
            if hasattr(e, 'code'):
                if e.code == 400:
                    raise AuthFailed(self, 'Invalid authorization code or expired (codes expire in ~1 min)')
                elif e.code == 401:
                    raise AuthFailed(self, 'Invalid client credentials')
                elif e.code == 411:
                    # Length Required - some Llave MX endpoints need empty body
                    logger.warning("request_access_token() Got 411, retrying with empty body")
                    # Retry logic could go here if needed
            
            raise AuthUnknownError(self, str(e))

    # ========================================================================
    # User Data Retrieval
    # ========================================================================
    
    def user_data(self, access_token, *args, **kwargs):
        """
        Fetch user data from Llave MX using access token.
        
        Llave MX uses custom 'accessToken' header (not standard Authorization: Bearer).
        
        Response structure:
        {
            "id": "123456",
            "curp": "AAAA000000HDFBBB00",
            "correo": "usuario@example.com",
            "nombre": "Juan",
            "primerApellido": "Pérez",
            "segundoApellido": "García",
            "telefono": "5512345678",
            "fechaNacimiento": "1990-01-15",
            "sexo": "H",
            "correoVerificado": true,
            "telefonoVerificado": true,
            "login": "AAAA000000HDFBBB00"
        }
        """
        headers = {
            "Content-Type": "application/json",
            "accessToken": access_token  # Llave MX specific header
        }
        
        url = self.USER_DATA_URL
        
        if VERBOSE_LOGGING:
            logger.info("user_data() URL: {url}".format(url=url))
            logger.info("user_data() access_token present: {present}".format(
                present=bool(access_token)
            ))
        
        try:
            request = Request(url, headers=headers, method='GET')
            response = urlopen(request)
            user_data = json.loads(response.read().decode('utf-8'))
            
            if VERBOSE_LOGGING:
                # Log without exposing sensitive data
                safe_data = {
                    k: v for k, v in user_data.items() 
                    if k not in ['curp', 'telefono']  # Don't log PII in production
                }
                logger.info("user_data() response: {data}".format(
                    data=json.dumps(safe_data, sort_keys=True, indent=2)
                ))
            
            # Validate response structure
            if not self.is_valid_llavemx_response(user_data):
                logger.error("user_data() Invalid response structure from Llave MX")
                raise AuthFailed(self, 'Invalid user data response from Llave MX')
            
            return user_data
            
        except Exception as e:
            logger.error("user_data() Exception: {error}".format(error=str(e)))
            
            if hasattr(e, 'code'):
                if e.code == 401:
                    raise AuthFailed(self, 'Invalid or expired access token')
                elif e.code == 403:
                    raise AuthFailed(self, 'Insufficient permissions')
            
            raise AuthUnknownError(self, str(e))

    def get_user_details(self, response):
        """
        Map Llave MX user data to Open edX user model AND MéxicoX custom fields.
        
        Mapping:
        - CURP → username (unique Mexican citizen identifier)
        - correo → email
        - nombre → first_name / nombres (MéxicoX custom)
        - primerApellido → primer_apellido (MéxicoX custom)
        - segundoApellido → segundo_apellido (MéxicoX custom)
        - estadoNacimiento → estado (MéxicoX custom)
        - domicilio.alcaldiaMunicipio → municipio (MéxicoX custom)
        
        Additional data stored in extra_data for profile extensions.
        """
        # Extract basic fields
        # Para cuentas básicas sin CURP, usar login (teléfono)
        curp = response.get("curp") or response.get("login", "")
        
        # Si no hay correo (cuentas básicas), generar uno temporal con el teléfono
        email = response.get("correo", "").strip()
        if not email:
            # Usar teléfono como email temporal
            phone = response.get("login") or response.get("telVigente", "")
            if phone:
                email = f"{phone}@llavemx.temp"
        
        first_name = response.get("nombre", "")
        
        # Extract apellidos (last names)
        primer_apellido = response.get("primerApellido", "")
        segundo_apellido = response.get("segundoApellido", "")
        
        # Combine apellidos for standard last_name field
        last_name = " ".join(
            part for part in [primer_apellido, segundo_apellido] if part
        ).strip()
        
        # Combine full name for frontend "name" field (required for auto-registration)
        full_name = " ".join(
            part for part in [first_name, primer_apellido, segundo_apellido] if part
        ).strip()
        
        # Extract domicilio (address) data
        domicilio = response.get("domicilio", {})
        municipio = domicilio.get("alcaldiaMunicipio", "") if domicilio else ""
        
        # Extract estado (state)
        estado_nacimiento = response.get("estadoNacimiento", "")
        
        # Build user details dict
        # Includes both standard Open edX fields AND MéxicoX custom fields
        n = datetime.now()
        user_details = {
            # Standard Open edX fields
            "id": response.get("idUsuario", ""),  # Usar idUsuario en vez de id
            "username": curp,  # CURP as username (unique in Mexico)
            "email": email,
            "name": full_name,  # Required by frontend for auto-registration
            "first_name": first_name,
            "last_name": last_name,
            
            # MéxicoX custom fields (match frontend form field names)
            "nombres": first_name,  # Frontend expects "nombres" not "first_name"
            "primer_apellido": primer_apellido,  # Frontend expects separate apellidos
            "segundo_apellido": segundo_apellido,
            "curp": curp,
            "estado": estado_nacimiento,  # Frontend expects "estado"
            "municipio": municipio,  # Frontend expects "municipio"
            
            # Additional Llave MX data
            "telefono": response.get("telefono", ""),
            "fechaNacimiento": response.get("fechaNacimiento", ""),
            "sexo": response.get("sexo", ""),
            "correoVerificado": response.get("correoVerificado", False),
            "telefonoVerificado": response.get("telefonoVerificado", False),
            "refresh_token": response.get("refresh_token", ""),
            "date_joined": str(n.isoformat())
        }
        
        if VERBOSE_LOGGING:
            # Log without PII
            safe_details = {
                k: v for k, v in user_details.items()
                if k not in ['curp', 'telefono', 'fechaNacimiento', 'refresh_token']
            }
            logger.info("get_user_details() returning: {details}".format(
                details=json.dumps(safe_details, sort_keys=True, indent=2)
            ))
        
        self._user_details = user_details
        return user_details

    # ========================================================================
    # User Update on Login
    # ========================================================================
    
    def update_user_details(self, user, user_details):
        """
        Update existing user data on each login.
        Keeps Open edX user data synchronized with Llave MX.
        """
        if not self.UPDATE_USER_ON_LOGIN:
            return
        
        try:
            updated_fields = []
            
            if user.first_name != user_details.get("first_name"):
                user.first_name = user_details["first_name"]
                updated_fields.append("first_name")
            
            if user.last_name != user_details.get("last_name"):
                user.last_name = user_details["last_name"]
                updated_fields.append("last_name")
            
            if user.email != user_details.get("email"):
                user.email = user_details["email"]
                updated_fields.append("email")
            
            if updated_fields:
                user.save()
                logger.info("update_user_details() Updated {fields} for user {username}".format(
                    fields=", ".join(updated_fields),
                    username=user.username
                ))
        except Exception as e:
            logger.error("update_user_details() Error updating user: {error}".format(
                error=str(e)
            ))

    # ========================================================================
    # Validation Helpers
    # ========================================================================
    
    def is_valid_dict(self, response, required_keys):
        """Check if response is a dict containing all required keys."""
        if not isinstance(response, dict):
            logger.warning("is_valid_dict() Expected dict but got {type}".format(
                type=type(response).__name__
            ))
            return False
        return all(key in response for key in required_keys)
    
    def is_valid_llavemx_response(self, response):
        """Validate Llave MX user data response structure."""
        # Llave MX usa "idUsuario" en vez de "id"
        required_keys = ["idUsuario", "nombre"]
        if not self.is_valid_dict(response, required_keys):
            return False
        
        # Debe tener correo O teléfono (para cuentas básicas sin correo)
        has_email = response.get("correo") and response.get("correo").strip()
        has_phone = response.get("login") or response.get("telVigente")
        
        return has_email or has_phone
    
    def is_llavemx_error(self, response):
        """Check if response is a Llave MX error."""
        error_keys = ["error", "error_description"]
        return self.is_valid_dict(response, error_keys)
    
    def is_token_response(self, response):
        """Validate token response structure."""
        required_keys = ["accessToken"]
        return self.is_valid_dict(response, required_keys)

    # ========================================================================
    # Optional: Role Management
    # ========================================================================
    
    def get_user_roles(self, access_token, user_id):
        """
        Fetch user roles from Llave MX (optional feature).
        
        Requires role management to be enabled in Llave MX app configuration.
        
        Request:
        POST /oauth/getRolesUsuarioLogueado
        {
            "idSistema": "<client_id>",
            "idUsuario": "<user_id>"
        }
        """
        if not access_token or not user_id:
            return []
        
        headers = {
            "Content-Type": "application/json",
            "accessToken": access_token
        }
        
        payload = {
            "idSistema": self.setting('KEY'),
            "idUsuario": str(user_id)
        }
        
        try:
            request = Request(
                self.ROLES_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            response = urlopen(request)
            roles_data = json.loads(response.read().decode('utf-8'))
            
            if VERBOSE_LOGGING:
                logger.info("get_user_roles() roles: {roles}".format(
                    roles=json.dumps(roles_data, indent=2)
                ))
            
            return roles_data.get("roles", [])
            
        except Exception as e:
            logger.warning("get_user_roles() Error fetching roles: {error}".format(
                error=str(e)
            ))
            return []

    # ========================================================================
    # Optional: Logout (SSO)
    # ========================================================================
    
    def logout(self, access_token):
        """
        Perform SSO logout in Llave MX.
        
        Request:
        POST /auth/cerrarSesion
        Headers: accessToken
        Body: {} (empty JSON object, required for some versions)
        
        Response:
        {
            "codeResponse": 101,
            "mensaje": "Logout success"
        }
        """
        if not access_token:
            logger.warning("logout() No access token provided")
            return False
        
        headers = {
            "Content-Type": "application/json",
            "accessToken": access_token
        }
        
        # Empty body required to avoid 411 Length Required error
        payload = {}
        
        try:
            request = Request(
                self.LOGOUT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            response = urlopen(request)
            logout_response = json.loads(response.read().decode('utf-8'))
            
            if VERBOSE_LOGGING:
                logger.info("logout() response: {response}".format(
                    response=json.dumps(logout_response, indent=2)
                ))
            
            code = logout_response.get("codeResponse")
            if code == 101:
                logger.info("logout() SSO logout successful")
                return True
            else:
                logger.warning("logout() Unexpected response code: {code}".format(
                    code=code
                ))
                return False
                
        except Exception as e:
            logger.error("logout() Error: {error}".format(error=str(e)))
            return False

    # ========================================================================
    # Properties (for backwards compatibility and logging)
    # ========================================================================
    
    @property
    def user_details(self):
        """Get cached user details."""
        return self._user_details
    
    @user_details.setter
    def user_details(self, value):
        """Set cached user details."""
        self._user_details = value
