Open edX OAuth2 Backend for Llave MX
=====================================

.. image:: https://img.shields.io/static/v1?label=pypi&style=flat-square&color=0475b6&message=edx-oauth2-llavemx
  :alt: PyPi edx-oauth2-llavemx
  :target: https://pypi.org/project/edx-oauth2-llavemx/

.. image:: https://img.shields.io/badge/Llave_MX-Mexican_Government-green.svg
  :target: https://www.gob.mx/llavemx
  :alt: Llave MX Official

|

Overview
--------

An Open edX OAuth2 + PKCE backend for `Llave MX <https://www.gob.mx/llavemx>`_, the official digital identity platform of the Mexican Government.

**Llave MX** allows users to authenticate in government services using a unified digital identity with verified CURP, email, and phone number.

Features
--------

- ✅ **OAuth 2.0 + PKCE** implementation (RFC 7636)
- ✅ **Custom JSON POST** for token exchange (Llave MX specific)
- ✅ **CURP as username** (Mexican unique citizen identifier)
- ✅ **Verified identity data** from government systems
- ✅ **Single Sign-On (SSO)** across government platforms
- ✅ **Automatic user data sync** on each login
- ✅ **Optional role management** integration
- ✅ **Comprehensive error handling** and logging
- ✅ **Production-ready** for Mexican government deployments

Key Differences from Standard OAuth2
-------------------------------------

Llave MX implements OAuth 2.0 with several non-standard customizations:

1. **Token endpoint requires JSON POST** (not form-encoded)
2. **Uses 'accessToken' header** instead of 'Authorization: Bearer'
3. **PKCE is mandatory** (code_challenge + code_verifier)
4. **Short token expiration** (15 minutes)
5. **Custom field names** in API responses

This backend handles all these differences automatically.

Llave MX Endpoints (VAL Environment)
-------------------------------------

This backend uses the validation/testing environment. For production, replace ``val-`` with production URLs.

**Authorization:**

.. code-block:: text

    https://val-llave.infotec.mx/oauth.xhtml

**Token Exchange:**

.. code-block:: text

    POST https://val-api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken

**User Data:**

.. code-block:: text

    GET https://val-api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario

**Roles (Optional):**

.. code-block:: text

    POST https://val-api-llave.infotec.mx/ws/rest/apps/oauth/getRolesUsuarioLogueado

**Logout (SSO):**

.. code-block:: text

    POST https://val-api-llave.infotec.mx/ws/rest/apps/auth/cerrarSesion


Installation
------------

1. Install from PyPI
~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    pip install edx-oauth2-llavemx

Or add to your ``requirements.txt``:

.. code-block:: text

    edx-oauth2-llavemx>=2.0.0


2. Configure Django Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add to your Django settings (``lms.env.json`` or ``cms.env.json`` in Open edX):

.. code-block:: python

    INSTALLED_APPS = [
        # ... other apps
        'oauth2_llavemx',
    ]

    AUTHENTICATION_BACKENDS = [
        'oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2',
        # ... other backends
    ]

    # Llave MX Configuration
    SOCIAL_AUTH_LLAVEMX_KEY = 'your_client_id'
    SOCIAL_AUTH_LLAVEMX_SECRET = 'your_client_secret'  # If required

    # Optional: Enable detailed logging
    LOGGING['loggers']['oauth2_llavemx'] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False,
    }


3. Setup with Tutor (Open edX)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Open edX deployments using Tutor:

.. code-block:: shell

    # Add the package
    tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS="edx-oauth2-llavemx"
    
    # Add to installed apps
    tutor config save --append ADDL_INSTALLED_APPS="oauth2_llavemx"
    
    # Add to authentication backends
    tutor config save --append THIRD_PARTY_AUTH_BACKENDS="oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"
    
    # Enable third-party authentication
    tutor config save --set ENABLE_THIRD_PARTY_AUTH=true
    
    # Rebuild Open edX image
    tutor images build openedx
    
    # Restart services
    tutor local restart


4. Register with Llave MX
~~~~~~~~~~~~~~~~~~~~~~~~~~

Before using this backend, you must register your application at:

.. code-block:: text

    https://val-llavemxintegracion.infotec.mx

**Requirements:**

- Institutional email (*@*.gob.mx*)
- System name and acronym
- Redirect URLs (callback URLs)
- Access policies (SSO, 2FA, phone/email verification)

**Important:** In production, only ``*.gob.mx`` domains are accepted.

After registration, you'll receive:

- ``client_id`` (use as ``SOCIAL_AUTH_LLAVEMX_KEY``)
- ``client_secret`` (if applicable)


5. Configure Third-Party Authentication in Open edX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to Django Admin: ``/admin/``
2. Navigate to **Third Party Authentication > Provider Configuration (OAuth)**
3. Click **Add Provider Configuration (OAuth)**
4. Fill in:

   - **Backend name:** ``llavemx``
   - **Client ID:** Your Llave MX client_id
   - **Client Secret:** Your client_secret (if required)
   - **Enabled:** ✓
   - **Skip registration form:** ✓ (optional)
   - **Skip email verification:** ✓ (Llave MX already verifies)

5. Save


Usage Example
-------------

Basic Implementation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

    # The backend is automatically registered when installed
    # Users can access it via:
    # - /login/llavemx
    # - /complete/llavemx (callback)


Custom Backend (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to customize the backend:

.. code-block:: python

    from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

    class MyCustomLlaveMX(LlaveMXOAuth2):
        name = "my-llavemx"
        
        # Override for production endpoints
        AUTHORIZATION_URL = "https://llave.infotec.mx/oauth.xhtml"
        ACCESS_TOKEN_URL = "https://api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken"
        USER_DATA_URL = "https://api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario"
        
        # Custom behavior
        def get_user_details(self, response):
            details = super().get_user_details(response)
            # Add custom logic
            return details


User Data Mapping
-----------------

Llave MX provides verified government data that is mapped to Open edX user fields:

.. code-block:: python

    # Llave MX Response → Open edX User
    {
        "curp": "AAAA000000HDFBBB00",      # → username (unique)
        "correo": "usuario@example.com",   # → email
        "nombre": "Juan",                  # → first_name
        "primerApellido": "Pérez",        # → last_name (part 1)
        "segundoApellido": "García",      # → last_name (part 2)
        "telefono": "5512345678",         # → stored in extra_data
        "fechaNacimiento": "1990-01-15",  # → stored in extra_data
        "sexo": "H",                      # → stored in extra_data
        "correoVerificado": true,         # → stored in extra_data
        "telefonoVerificado": true        # → stored in extra_data
    }

**Note:** CURP is used as the username because it's unique and permanent for Mexican citizens.


OAuth Flow
----------

1. User clicks "Login with Llave MX" in Open edX
2. Open edX redirects to ``https://val-llave.infotec.mx/oauth.xhtml``
3. User authenticates with Llave MX credentials
4. Llave MX redirects back with authorization code
5. Backend exchanges code for access token (with PKCE verification)
6. Backend fetches user data from Llave MX API
7. Open edX creates or updates user account
8. User is logged in


PKCE Implementation
-------------------

This backend implements OAuth 2.0 with PKCE (Proof Key for Code Exchange) as required by Llave MX:

1. **Generate code_verifier** (random 43-128 character string)
2. **Generate code_challenge** = BASE64URL(SHA256(code_verifier))
3. **Send code_challenge** in authorization request
4. **Send code_verifier** in token exchange
5. **Llave MX verifies** challenge matches verifier

PKCE prevents authorization code interception attacks.


Configuration Options
---------------------

Available settings (prefix with ``SOCIAL_AUTH_LLAVEMX_``):

.. code-block:: python

    # Required
    SOCIAL_AUTH_LLAVEMX_KEY = 'your_client_id'
    
    # Optional
    SOCIAL_AUTH_LLAVEMX_SECRET = 'your_secret'  # If required by your app
    
    # Callback URL (auto-generated, but can override)
    SOCIAL_AUTH_LLAVEMX_REDIRECT_URI = 'https://yourdomain.gob.mx/auth/complete/llavemx/'
    
    # Additional backend settings
    SOCIAL_AUTH_LLAVEMX_UPDATE_USER_ON_LOGIN = True  # Sync user data on each login


Error Handling
--------------

The backend handles common Llave MX errors:

**invalid_grant**
    Authorization code expired or invalid (codes expire in ~1 minute)

**invalid_client**
    Client ID or secret incorrect, or app not authorized

**invalid_token**
    Access token expired (15 minute lifetime), revoked, or invalid

**redirect_uri_mismatch**
    Callback URL doesn't match registered URL in Llave MX

All errors are logged with detailed information for debugging.


Logging
-------

Enable detailed logging for debugging:

.. code-block:: python

    LOGGING = {
        'loggers': {
            'oauth2_llavemx': {
                'level': 'INFO',  # or 'DEBUG' for more detail
                'handlers': ['console', 'file'],
                'propagate': False,
            },
        },
    }

Logs include:

- Authorization URLs and parameters (without exposing tokens)
- Token exchange requests/responses
- User data retrieval
- PKCE challenge/verifier generation
- Error details with context


Testing
-------

Run the test suite:

.. code-block:: shell

    # Install development dependencies
    pip install -e ".[dev]"
    
    # Run tests
    python tests/test_llavemx.py
    
    # Or with pytest
    pytest tests/test_llavemx.py -v


Security Considerations
-----------------------

1. **HTTPS Required:** All communication with Llave MX must use HTTPS
2. **Token Storage:** Access tokens expire in 15 minutes
3. **PKCE:** Mandatory for security (prevents code interception)
4. **IP Whitelisting:** Register your server's public IP with Llave MX
5. **Domain Restrictions:** Production only accepts ``*.gob.mx`` domains
6. **PII Handling:** CURP and phone numbers are sensitive personal data
7. **Logging:** Never log full tokens or sensitive user data in production


Production Deployment
---------------------

For production deployments:

1. **Use production endpoints** (remove ``val-`` prefix)
2. **Register ``*.gob.mx`` domain** with Llave MX
3. **Whitelist server IPs** with ATDT (Agencia de Transformación Digital)
4. **Enable HTTPS** on all URLs
5. **Configure proper logging** (without exposing PII)
6. **Set up monitoring** for token expiration and auth failures
7. **Test SSO logout** flow if implemented


Optional Features
-----------------

Role Management
~~~~~~~~~~~~~~~

If role management is enabled in your Llave MX app:

.. code-block:: python

    # In your custom backend
    def user_data(self, access_token, *args, **kwargs):
        data = super().user_data(access_token, *args, **kwargs)
        
        # Fetch roles
        user_id = data.get('id')
        roles = self.get_user_roles(access_token, user_id)
        data['roles'] = roles
        
        return data


SSO Logout
~~~~~~~~~~

To implement single sign-out:

.. code-block:: python

    # In your logout view
    from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2
    
    backend = LlaveMXOAuth2()
    access_token = user.social_auth.get(provider='llavemx').extra_data['access_token']
    backend.logout(access_token)


Support
-------

- **Issues:** https://github.com/aprendemx/Edx-Oauth2/issues
- **Llave MX Documentation:** https://www.gob.mx/llavemx
- **Open edX:** https://discuss.openedx.org/


License
-------

MIT License - See LICENSE.txt


Changelog
---------

Version 2.0.0 (2025-10-31)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Initial release of Llave MX backend
- OAuth 2.0 + PKCE implementation
- Custom JSON POST token exchange
- CURP-based username mapping
- Comprehensive error handling
- Role management support
- SSO logout implementation
- Full test suite


Contributing
------------

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request


Authors
-------

- AprendeMX Team
- OAuth2 + PKCE implementation for Llave MX
