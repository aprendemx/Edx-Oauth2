Open edX OAuth2 Backend for Llave MXOpen edX OAuth2 Backend for Llave MX

==========================================================================



.. image:: https://img.shields.io/static/v1?logo=discourse&label=Discussions&style=flat-square&color=ff0080&message=OpenEdx.. image:: https://img.shields.io/static/v1?logo=discourse&label=Discussions&style=flat-square&color=ff0080&message=OpenEdx

  :alt: Open edX Discussions  :alt: Open edX Discussions

  :target: https://discuss.openedx.org/  :target: https://discuss.openedx.org/



||





OverviewOverview

----------------



An Open edX OAuth2 backend for `Llave MX <https://www.gob.mx/llavemx>`_, the Mexican Government's digital identity platform.An Open edX OAuth2 backend for `Llave MX <https://www.gob.mx/llavemx>`_, the Mexican Government's digital identity platform.



This package provides secure government authentication integration with Open edX using OAuth 2.0 + PKCE (Proof Key for Code Exchange).- `Python Social Auth custom backend implementation <https://python-social-auth.readthedocs.io/en/latest/backends/implementation.html>`_

- OAuth 2.0 with PKCE (Proof Key for Code Exchange) RFC 7636

- `Python Social Auth custom backend implementation <https://python-social-auth.readthedocs.io/en/latest/backends/implementation.html>`_- CURP-based user authentication and registration

- OAuth 2.0 with PKCE (RFC 7636)

- CURP-based user authentication and registrationThis is a secure implementation that integrates Llave MX government digital identity authentication with Open edX.

It includes comprehensive logging, PKCE security, and supports both Mexican nationals and foreign residents.



Features

--------Features

--------

- **OAuth 2.0 + PKCE**: Full implementation with SHA256 code challenge

- **Government Authentication**: Integration with Mexican government digital identity (Llave MX)- **OAuth 2.0 + PKCE**: Full implementation with SHA256 code challenge

- **CURP Support**: Uses CURP (Clave Única de Registro de Población) as username- **Government Authentication**: Integration with Mexican government digital identity (Llave MX)

- **User Types**: Supports Mexican nationals, foreign residents, and unverified users- **CURP Support**: Uses CURP (Clave Única de Registro de Población) as username

- **Security**: PKCE mandatory, HTTPS enforcement, 15-minute token expiration- **User Types**: Supports Mexican nationals, foreign residents, and unverified users

- **Comprehensive Logging**: Detailed logs for debugging (with PII protection)- **Security**: PKCE mandatory, HTTPS enforcement, 15-minute token expiration

- **Comprehensive Logging**: Detailed logs for debugging (with PII protection)



Installation

------------Installation

------------

1. Install the package

~~~~~~~~~~~~~~~~~~~~~~1. Install the package

~~~~~~~~~~~~~~~~~~~~~~

Add to your requirements.txt or install from the command line:

Add to your requirements.txt or install from the command line:

..  code-block:: shell

..  code-block:: shell

  pip install git+https://github.com/aprendemx/Edx-Oauth2.git

  pip install git+https://github.com/aprendemx/Edx-Oauth2.git



2. Configure Open edX with Tutor

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~2. Configure Open edX with Tutor

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

.. code-block:: shell

     tutor config save --append ADDL_INSTALLED_APPS="oauth2_llavemx"

     tutor config save --append THIRD_PARTY_AUTH_BACKENDS="oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"     tutor config save --append ADDL_INSTALLED_APPS="oauth2_llavemx"

     tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS="git+https://github.com/aprendemx/Edx-Oauth2.git"     tutor config save --append THIRD_PARTY_AUTH_BACKENDS="oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"

     tutor images build openedx     tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS="git+https://github.com/aprendemx/Edx-Oauth2.git"

     tutor local restart     tutor images build openedx





3. Django Settings Configuration3. Django Settings Configuration

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



Add to your Open edX Django settings:Add to your Open edX Django settings:



..  code-block:: yaml..  code-block:: yaml



  ADDL_INSTALLED_APPS:  ADDL_INSTALLED_APPS:

  - "oauth2_llavemx"  - "oauth2_llavemx"

    

  THIRD_PARTY_AUTH_BACKENDS:  THIRD_PARTY_AUTH_BACKENDS:

  - "oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"  - "oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"

    

  ENABLE_REQUIRE_THIRD_PARTY_AUTH: true  ENABLE_REQUIRE_THIRD_PARTY_AUTH: true





4. LMS Admin Configuration4. LMS Admin Configuration

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



Configure in Django Admin → Third Party Authentication → Provider Configuration (OAuth):Configure in Django Admin → Third Party Authentication → Provider Configuration (OAuth):



.. list-table:: Llave MX OAuth Setup.. list-table:: Llave MX OAuth Setup

  :widths: 50 100  :widths: 50 100

  :header-rows: 1  :header-rows: 1



  * - Key  * - Key

    - Value    - Value

  * - Backend name  * - Backend name

    - llavemx-oauth    - llavemx-oauth

  * - Client ID  * - Client ID

    - (Provided by Llave MX)    - (Provided by Llave MX)

  * - Client Secret  * - Client Secret

    - (Provided by Llave MX)    - (Provided by Llave MX)

  * - Enabled  * - Authorization URL

    - ✓ (checked)    - https://val-llave.infotec.mx/oauth.xhtml (testing) or https://llavemx.gob.mx/oauth.xhtml (production)

  * - Skip registration form  * - Access Token URL

    - ✓ (optional)    - https://val-api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken (testing)

  * - Skip email verification  *   * - User API URL

    - ✓ (optional)    - https://val-api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario (testing)





Llave MX EnvironmentsSecurity Features

---------------------    - https://web.stepwisemath.ai/auth/complete/stepwisemath-oauth



Testing Environment (val-llave)4. Configure a new Oauth2 client from the lms Django Admin console

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



- Authorization URL: ``https://val-llave.infotec.mx/oauth.xhtml``.. image:: https://raw.githubusercontent.com/lpm0073/edx-oauth2-wordpress-backend/main/doc/django-admin-1.png

- Access Token URL: ``https://val-api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken``  :width: 100%

- User Data URL: ``https://val-api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario``  :alt: Open edX Django Admin Add Provider Configuration (OAuth)



Production Environment.. image:: https://raw.githubusercontent.com/lpm0073/edx-oauth2-wordpress-backend/main/doc/django-admin-2.png

~~~~~~~~~~~~~~~~~~~~~~  :width: 100%

  :alt: Open edX Django Admin Add Provider Configuration (OAuth)

- Authorization URL: ``https://llavemx.gob.mx/oauth.xhtml``

- Access Token URL: ``https://api-llave.gob.mx/ws/rest/apps/oauth/obtenerToken``

- User Data URL: ``https://api-llave.gob.mx/ws/rest/apps/oauth/datosUsuario``Cookiecutter openedx_devops deployment



..  code-block:: shell

Security Features

-----------------  tutor config save --set OPENEDX_WPOAUTH_BACKEND_BASE_URL="${{ secrets.WPOAUTH_BACKEND_BASE_URL }}" \

                    --set OPENEDX_WPOAUTH_BACKEND_CLIENT_ID="${{ secrets.WPOAUTH_BACKEND_CLIENT_ID }}" \

- **PKCE (RFC 7636)**: Mandatory code challenge with SHA256                    --set OPENEDX_WPOAUTH_BACKEND_CLIENT_SECRET="${{ secrets.WPOAUTH_BACKEND_CLIENT_SECRET }}"

- **HTTPS Only**: All communications encrypted

- **Token Expiration**: 15-minute access token lifetimeWP Oauth Plugin Configuration

- **PII Protection**: CURP and phone numbers excluded from standard logs-----------------------------

- **State Parameter**: CSRF protection enabled

- **Input Validation**: Comprehensive validation of all Llave MX responsesThis plugin enables your Open edX installation to authenticate against the WP Oauth plugin provider

in your Wordpress web site, configured as follows:



Architecture.. image:: https://raw.githubusercontent.com/lpm0073/edx-oauth2-wordpress-backend/main/doc/wp-oauth-config.png

------------  :width: 100%

  :alt: WP OAuth Server configuration page

OAuth 2.0 Flow

~~~~~~~~~~~~~~Sample lms log output

---------------------

1. **User initiates login**: User clicks "Login with Llave MX"

2. **PKCE generation**: System generates code verifier and challenge

3. **Authorization request**: User redirected to Llave MX with challenge..  code-block:: shell

4. **User authenticates**: User logs in with government credentials

5. **Authorization code**: Llave MX returns code to callback URL    2022-10-06 20:17:08,832 INFO 19 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/auth/login/stepwisemath-oauth/", "context": {"user_id": null, "path": "/auth/login/stepwisemath-oauth/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/login", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {\"auth_entry\": [\"login\"], \"next\": [\"/dashboard\"]}, \"POST\": {}}", "time": "2022-10-06T20:17:08.832684+00:00", "event_type": "/auth/login/stepwisemath-oauth/", "event_source": "server", "page": null}

6. **Token exchange**: Backend exchanges code + verifier for access token    2022-10-06 20:17:09,230 INFO 19 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:216 - AUTHORIZATION_URL: https://stepwisemath.ai/oauth/authorize

7. **User data retrieval**: Backend fetches user data with access token    [pid: 19|app: 0|req: 2/19] 192.168.4.4 () {68 vars in 1889 bytes} [Thu Oct  6 20:17:08 2022] GET /auth/login/stepwisemath-oauth/?auth_entry=login&next=%2Fdashboard => generated 0 bytes in 430 msecs (HTTP/1.1 302) 9 headers in 922 bytes (1 switches on core 0)

8. **User creation/login**: Open edX creates or logs in user with CURP    2022-10-06 20:17:38,485 INFO 7 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/auth/complete/stepwisemath-oauth/", "context": {"user_id": null, "path": "/auth/complete/stepwisemath-oauth/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://stepwisemath.ai/", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {\"redirect_state\": [\"pdbIKIcEbhjVr3Kon5VXUWWiy5kuX921\"], \"code\": [\"q0antmap4qfamd6pe24jh75pdprahpdiyitmut0o\"], \"state\": [\"pdbIKIcEbhjVr3Kon5VXUWWiy5kuX921\"], \"iframe\": [\"break\"]}, \"POST\": {}}", "time": "2022-10-06T20:17:38.484675+00:00", "event_type": "/auth/complete/stepwisemath-oauth/", "event_source": "server", "page": null}

    2022-10-06 20:17:38,496 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:223 - ACCESS_TOKEN_URL: https://stepwisemath.ai/oauth/token

    2022-10-06 20:17:40,197 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:230 - USER_QUERY: https://stepwisemath.ai/oauth/me

User Data Mapping    2022-10-06 20:17:40,197 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:363 - user_data() url: https://stepwisemath.ai/oauth/me?access_token=jx2zql9fw2jx9s7tayik4ybfjrmuhb7m5csb1mtl

~~~~~~~~~~~~~~~~~    2022-10-06 20:17:41,965 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:368 - user_data() response: {

        "ID": "7",

.. list-table:: Llave MX to Open edX Field Mapping        "display_name": "Test McBugster",

  :widths: 40 40 20        "user_email": "test@stepwisemath.ai",

  :header-rows: 1        "user_login": "testaccount",

        "user_nicename": "testaccount",

  * - Llave MX Field        "user_registered": "2022-10-06 19:57:56",

    - Open edX Field        "user_roles": [

    - Required            "administrator"

  * - curp        ],

    - username        "user_status": "0"

    - ✓    }

  * - email    2022-10-06 20:17:41,966 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:269 - get_user_details() received wp-oauth user data response json dict: {

    - email        "ID": "7",

    - ✓        "display_name": "Test McBugster",

  * - nombre        "user_email": "test@stepwisemath.ai",

    - first_name        "user_login": "testaccount",

    - ✓        "user_nicename": "testaccount",

  * - primerApellido        "user_registered": "2022-10-06 19:57:56",

    - last_name        "user_roles": [

    - ✓            "administrator"

  * - segundoApellido        ],

    - last_name (appended)        "user_status": "0"

    -     }

  * - fechaNacimiento    2022-10-06 20:17:41,966 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:317 - get_user_details() processing response object

    - profile.year_of_birth    2022-10-06 20:17:41,966 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:241 - user_details.setter: new value set {

    -         "date_joined": "2022-10-06 19:57:56",

  * - telefono        "email": "test@stepwisemath.ai",

    - profile.phone_number        "first_name": "Test",

    -         "fullname": "Test McBugster",

        "id": 7,

        "is_staff": true,

Testing        "is_superuser": true,

-------        "last_name": "McBugster",

        "refresh_token": "",

Run the test suite:        "scope": "",

        "token_type": "",

..  code-block:: shell        "user_status": "0",

        "username": "testaccount"

  cd /Users/diegonicolas/Desktop/oauth/Edx-Oauth2    }

  python -m pytest tests/test_llavemx.py -v    2022-10-06 20:17:41,967 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:345 - get_user_details() returning: {

        "date_joined": "2022-10-06 19:57:56",

        "email": "test@stepwisemath.ai",

Documentation        "first_name": "Test",

-------------        "fullname": "Test McBugster",

        "id": 7,

For detailed documentation, see:        "is_staff": true,

        "is_superuser": true,

- `README_LLAVEMX.rst <./README_LLAVEMX.rst>`_ - Complete implementation guide        "last_name": "McBugster",

- `TESTING.md <./TESTING.md>`_ - Testing instructions        "refresh_token": "",

- `CHANGELOG_LLAVEMX.md <./CHANGELOG_LLAVEMX.md>`_ - Version history        "scope": "",

        "token_type": "",

        "user_status": "0",

Support        "username": "testaccount"

-------    }

    2022-10-06 20:17:41,972 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:269 - get_user_details() received extended get_user_details() return dict: {

- `Open edX Discussions <https://discuss.openedx.org/>`_        "access_token": "jx2zql9fw2jx9s7tayik4ybfjrmuhb7m5csb1mtl",

- `GitHub Issues <https://github.com/aprendemx/Edx-Oauth2/issues>`_        "date_joined": "2022-10-06 19:57:56",

        "email": "test@stepwisemath.ai",

        "expires_in": 3600,

License        "first_name": "Test",

-------        "fullname": "Test McBugster",

        "id": 7,

Licensed under the terms of the `GNU Affero General Public License (AGPL) <./LICENSE.txt>`_.        "is_staff": true,

        "is_superuser": true,
        "last_name": "McBugster",
        "refresh_token": "",
        "scope": "",
        "token_type": "",
        "user_status": "0",
        "username": "testaccount"
    }
    2022-10-06 20:17:41,973 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:241 - user_details.setter: new value set {
        "access_token": "jx2zql9fw2jx9s7tayik4ybfjrmuhb7m5csb1mtl",
        "date_joined": "2022-10-06 19:57:56",
        "email": "test@stepwisemath.ai",
        "expires_in": 3600,
        "first_name": "Test",
        "fullname": "Test McBugster",
        "id": 7,
        "is_staff": true,
        "is_superuser": true,
        "last_name": "McBugster",
        "refresh_token": "",
        "scope": "",
        "token_type": "",
        "user_status": "0",
        "username": "testaccount"
    }
    2022-10-06 20:17:41,973 INFO 7 [oauth2_wordpress.wp_oauth] [user None] [ip 192.168.6.26] wp_oauth.py:290 - get_user_details() returning extended get_user_details() return dict: {
        "access_token": "jx2zql9fw2jx9s7tayik4ybfjrmuhb7m5csb1mtl",
        "date_joined": "2022-10-06 19:57:56",
        "email": "test@stepwisemath.ai",
        "expires_in": 3600,
        "first_name": "Test",
        "fullname": "Test McBugster",
        "id": 7,
        "is_staff": true,
        "is_superuser": true,
        "last_name": "McBugster",
        "refresh_token": "",
        "scope": "",
        "token_type": "",
        "user_status": "0",
        "username": "testaccount"
    }
    [pid: 7|app: 0|req: 2/20] 192.168.4.4 () {70 vars in 2136 bytes} [Thu Oct  6 20:17:38 2022] GET /auth/complete/stepwisemath-oauth/?redirect_state=pdbIKIcEbhjVr3Kon5VXUWWiy5kuX921&code=q0antmap4qfamd6pe24jh75pdprahpdiyitmut0o&state=pdbIKIcEbhjVr3Kon5VXUWWiy5kuX921&iframe=break => generated 0 bytes in 3549 msecs (HTTP/1.1 302) 9 headers in 612 bytes (1 switches on core 0)
    2022-10-06 20:17:42,211 INFO 19 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/register", "context": {"user_id": null, "path": "/register", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://stepwisemath.ai/", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {}}", "time": "2022-10-06T20:17:42.211436+00:00", "event_type": "/register", "event_source": "server", "page": null}
    [pid: 19|app: 0|req: 3/21] 192.168.4.4 () {70 vars in 1796 bytes} [Thu Oct  6 20:17:42 2022] GET /register => generated 37606 bytes in 177 msecs (HTTP/1.1 200) 8 headers in 600 bytes (1 switches on core 0)
    2022-10-06 20:17:42,527 INFO 7 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/stepwise/api/v1/configuration/prod", "context": {"user_id": null, "path": "/stepwise/api/v1/configuration/prod", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {}}", "time": "2022-10-06T20:17:42.527217+00:00", "event_type": "/stepwise/api/v1/configuration/prod", "event_source": "server", "page": null}
    [pid: 7|app: 0|req: 3/22] 192.168.4.4 () {68 vars in 1755 bytes} [Thu Oct  6 20:17:42 2022] GET /stepwise/api/v1/configuration/prod => generated 167 bytes in 41 msecs (HTTP/1.1 200) 6 headers in 189 bytes (1 switches on core 0)
    2022-10-06 20:17:42,617 INFO 19 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/api/user/v2/account/registration/", "context": {"user_id": null, "path": "/api/user/v2/account/registration/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {\"next\": [\"/dashboard\"], \"email\": [\"test@stepwisemath.ai\"], \"name\": [\"Test McBugster\"], \"username\": [\"testaccount\"], \"password\": \"********\", \"level_of_education\": [\"\"], \"gender\": [\"\"], \"year_of_birth\": [\"\"], \"mailing_address\": [\"\"], \"goals\": [\"\"], \"social_auth_provider\": [\"Stepwise\"], \"terms_of_service\": [\"true\"]}}", "time": "2022-10-06T20:17:42.616767+00:00", "event_type": "/api/user/v2/account/registration/", "event_source": "server", "page": null}
    2022-10-06 20:17:42,620 INFO 7 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/api/user/v1/validation/registration", "context": {"user_id": null, "path": "/api/user/v1/validation/registration", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {\"name\": [\"Test McBugster\"], \"username\": [\"testaccount\"], \"password\": \"********\", \"email\": [\"test@stepwisemath.ai\"], \"terms_of_service\": [\"false\"]}}", "time": "2022-10-06T20:17:42.619453+00:00", "event_type": "/api/user/v1/validation/registration", "event_source": "server", "page": null}
    [pid: 7|app: 0|req: 4/23] 192.168.4.4 () {74 vars in 1928 bytes} [Thu Oct  6 20:17:42 2022] POST /api/user/v1/validation/registration => generated 205 bytes in 85 msecs (HTTP/1.1 200) 8 headers in 282 bytes (1 switches on core 0)
    2022-10-06 20:17:42,719 INFO 7 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/api/user/v1/validation/registration", "context": {"user_id": null, "path": "/api/user/v1/validation/registration", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {\"name\": [\"Test McBugster\"], \"username\": [\"testaccount\"], \"password\": \"********\", \"email\": [\"test@stepwisemath.ai\"], \"terms_of_service\": [\"false\"]}}", "time": "2022-10-06T20:17:42.719504+00:00", "event_type": "/api/user/v1/validation/registration", "event_source": "server", "page": null}
    [pid: 7|app: 0|req: 5/24] 192.168.4.4 () {74 vars in 1928 bytes} [Thu Oct  6 20:17:42 2022] POST /api/user/v1/validation/registration => generated 205 bytes in 102 msecs (HTTP/1.1 200) 8 headers in 282 bytes (1 switches on core 0)
    2022-10-06 20:17:42,816 INFO 7 [tracking] [user None] [ip 192.168.6.26] logger.py:41 - {"name": "/api/user/v1/validation/registration", "context": {"user_id": null, "path": "/api/user/v1/validation/registration", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {\"name\": [\"Test McBugster\"], \"username\": [\"testaccount\"], \"password\": \"********\", \"email\": [\"test@stepwisemath.ai\"], \"terms_of_service\": [\"false\"]}}", "time": "2022-10-06T20:17:42.816042+00:00", "event_type": "/api/user/v1/validation/registration", "event_source": "server", "page": null}
    [pid: 7|app: 0|req: 6/25] 192.168.4.4 () {74 vars in 1928 bytes} [Thu Oct  6 20:17:42 2022] POST /api/user/v1/validation/registration => generated 205 bytes in 77 msecs (HTTP/1.1 200) 8 headers in 282 bytes (1 switches on core 0)
    2022-10-06 20:17:43,160 INFO 19 [audit] [user 53] [ip 192.168.6.26] models.py:2753 - Login success - user.id: 53
    2022-10-06 20:17:43,221 INFO 19 [tracking] [user 53] [ip 192.168.6.26] logger.py:41 - {"name": "edx.user.settings.changed", "context": {"user_id": null, "path": "/api/user/v2/account/registration/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": {"old": null, "new": "en", "truncated": [], "setting": "pref-lang", "user_id": 53, "table": "user_api_userpreference"}, "time": "2022-10-06T20:17:43.220899+00:00", "event_type": "edx.user.settings.changed", "event_source": "server", "page": null}
    2022-10-06 20:17:43,239 INFO 19 [tracking] [user 53] [ip 192.168.6.26] logger.py:41 - {"name": "edx.user.settings.changed", "context": {"user_id": null, "path": "/api/user/v2/account/registration/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "", "session": "a3f4ac2a5bf97f717f5745984059891b", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": {"old": false, "new": true, "truncated": [], "setting": "is_active", "user_id": 53, "table": "auth_user"}, "time": "2022-10-06T20:17:43.238965+00:00", "event_type": "edx.user.settings.changed", "event_source": "server", "page": null}
    /openedx/venv/lib/python3.8/site-packages/django/db/models/fields/__init__.py:1416: RuntimeWarning: DateTimeField Registration.activation_timestamp received a naive datetime (2022-10-06 20:17:43.246811) while time zone support is active.
      warnings.warn("DateTimeField %s received a naive datetime (%s)"
    2022-10-06 20:17:43,254 INFO 19 [common.djangoapps.student.models] [user 53] [ip 192.168.6.26] models.py:938 - User testaccount (test@stepwisemath.ai) account is successfully activated.
    2022-10-06 20:17:43,255 INFO 19 [openedx_events.tooling] [user 53] [ip 192.168.6.26] tooling.py:160 - Responses of the Open edX Event <org.openedx.learning.student.registration.completed.v1>:
    []
    2022-10-06 20:17:43,261 INFO 19 [audit] [user 53] [ip 192.168.6.26] register.py:295 - Login success on new account creation - testaccount
    [pid: 19|app: 0|req: 4/26] 192.168.4.4 () {74 vars in 1881 bytes} [Thu Oct  6 20:17:42 2022] POST /api/user/v2/account/registration/ => generated 79 bytes in 1145 msecs (HTTP/1.1 200) 15 headers in 3254 bytes (1 switches on core 0)
    2022-10-06 20:17:44,014 INFO 7 [tracking] [user 53] [ip 192.168.6.26] logger.py:41 - {"name": "/auth/complete/stepwisemath-oauth/", "context": {"user_id": 53, "path": "/auth/complete/stepwisemath-oauth/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "testaccount", "session": "4b87c052d7ba72c52f84c82737834d90", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {}}", "time": "2022-10-06T20:17:44.014681+00:00", "event_type": "/auth/complete/stepwisemath-oauth/", "event_source": "server", "page": null}
    /openedx/venv/lib/python3.8/site-packages/django/db/models/fields/__init__.py:1416: RuntimeWarning: DateTimeField User.date_joined received a naive datetime (2022-10-06 19:57:56) while time zone support is active.
      warnings.warn("DateTimeField %s received a naive datetime (%s)"
    2022-10-06 20:17:44,100 INFO 7 [tracking] [user 53] [ip 192.168.6.26] logger.py:41 - {"name": "edx.user.settings.changed", "context": {"user_id": 53, "path": "/auth/complete/stepwisemath-oauth/", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "testaccount", "session": "4b87c052d7ba72c52f84c82737834d90", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": {"old": "2022-10-06T20:17:42.674048+00:00", "new": "2022-10-06 19:57:56", "truncated": [], "setting": "date_joined", "user_id": 53, "table": "auth_user"}, "time": "2022-10-06T20:17:44.100229+00:00", "event_type": "edx.user.settings.changed", "event_source": "server", "page": null}
    [pid: 7|app: 0|req: 7/27] 192.168.4.4 () {66 vars in 3727 bytes} [Thu Oct  6 20:17:43 2022] GET /auth/complete/stepwisemath-oauth/? => generated 0 bytes in 150 msecs (HTTP/1.1 302) 10 headers in 721 bytes (1 switches on core 0)
    2022-10-06 20:17:44,375 INFO 19 [tracking] [user 53] [ip 192.168.6.26] logger.py:41 - {"name": "/dashboard", "context": {"user_id": 53, "path": "/dashboard", "course_id": "", "org_id": "", "enterprise_uuid": ""}, "username": "testaccount", "session": "4b87c052d7ba72c52f84c82737834d90", "ip": "192.168.6.26", "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "host": "web.stepwisemath.ai", "referer": "https://web.stepwisemath.ai/register", "accept_language": "en-US,en;q=0.9,es-MX;q=0.8,es-US;q=0.7,es;q=0.6", "event": "{\"GET\": {}, \"POST\": {}}", "time": "2022-10-06T20:17:44.374973+00:00", "event_type": "/dashboard", "event_source": "server", "page": null}
