# CHANGE LOG

## Version 2.0.0 (2025-10-31) - Llave MX Release 🎉

### Major Changes

- **NEW:** Complete Llave MX OAuth2 + PKCE backend implementation
- **NEW:** `oauth2_llavemx` package replaces `oauth2_nem`
- **BREAKING:** Package renamed from `edx-oauth2-nem` to `edx-oauth2-llavemx`
- **BREAKING:** Backend class renamed to `LlaveMXOAuth2`
- **BREAKING:** Backend identifier changed from `nem-oauth` to `llavemx`

### Features Added

- ✅ OAuth 2.0 + PKCE (RFC 7636) implementation
- ✅ Custom JSON POST token exchange (Llave MX specific)
- ✅ CURP-based username mapping
- ✅ Verified government identity data
- ✅ Comprehensive error handling
- ✅ Role management support (optional)
- ✅ SSO logout implementation
- ✅ Automatic user data sync on login
- ✅ Detailed logging (without exposing PII)
- ✅ Full test suite with fixtures
- ✅ Production-ready for Mexican government

### Security Improvements

- PKCE mandatory (prevents code interception)
- Secure code_verifier generation (cryptographically random)
- SHA256 code challenge method
- Token expiration handling (15 min)
- IP whitelisting support
- HTTPS enforcement
- PII protection in logs

### API Changes

**Endpoints (VAL environment):**
- Authorization: `https://val-llave.infotec.mx/oauth.xhtml`
- Token: `https://val-api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken`
- User Data: `https://val-api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario`
- Roles: `https://val-api-llave.infotec.mx/ws/rest/apps/oauth/getRolesUsuarioLogueado`
- Logout: `https://val-api-llave.infotec.mx/ws/rest/apps/auth/cerrarSesion`

**Request Format:**
- Token request now uses POST with JSON body
- Custom 'accessToken' header for API calls
- PKCE parameters in authorization

**Response Mapping:**
- `curp` → `username` (was `email`)
- `nombre` → `first_name`
- `primerApellido + segundoApellido` → `last_name`
- `correo` → `email`
- Additional fields stored in `extra_data`

### Documentation

- ✅ Complete README_LLAVEMX.rst
- ✅ MIGRATION_GUIDE.md for upgrading from NEM
- ✅ Inline code documentation
- ✅ Test fixtures and examples
- ✅ Configuration examples for Tutor

### Testing

- ✅ Unit tests for validation methods
- ✅ User data mapping tests
- ✅ PKCE generation tests
- ✅ Error handling tests
- ✅ Test fixtures for all scenarios
- ✅ Mock-based integration tests

### Backward Compatibility

- `oauth2_nem` package retained with deprecation warning
- Compatibility import redirects to `oauth2_llavemx`
- Migration guide provided
- Database migration instructions included

### Dependencies

- `social-auth-core>=4.3.0`
- `social-auth-app-django>=5.0.0`
- Python 3.7+
- Django 2.2+

---

## Version 1.0.22 (2024-02-01) - NEM (Previous)

- NEM backend implementation
- Basic OAuth2 support
- WordPress WP OAuth integration

## Version 1.0.8 (2024-02-01)

- Add support for UPDATE_USER_ON_LOGIN flag

## Version 1.0.7 (2023-08-12)

- Match version requirements in pyproject.toml to those in requirements/stable-psa.txt

## Version 1.0.6 (2022-12-20)

- Standardize usage of python3 in Makefile

## Version 1.0.5 (2022-12-20)

- Version bumps

## Version 1.0.4 (2022-11-09)

- Add property for URL
- Add class variables for PATH, AUTHORIZATION_ENDPOINT, TOKEN_ENDPOINT, USERINFO_ENDPOINT
- Switch to urllib.parse urljoin()
- Add a Makefile

---

## Migration Notes

To upgrade from v1.x (NEM) to v2.0 (Llave MX), see MIGRATION_GUIDE.md

Key steps:
1. Install `edx-oauth2-llavemx`
2. Update Django settings
3. Update Third-Party Auth provider configuration
4. Migrate database records (optional)
5. Test thoroughly

## Future Roadmap

### v2.1.0 (Planned)
- [ ] Refresh token automatic renewal
- [ ] Enhanced role mapping to Open edX groups
- [ ] Production endpoint configuration helpers
- [ ] Performance optimizations

### v2.2.0 (Planned)
- [ ] Multi-factor authentication support
- [ ] Phone verification workflow
- [ ] Minor/foreigner policy support
- [ ] Enhanced audit logging

## Support

For questions or issues:
- GitHub Issues: https://github.com/aprendemx/Edx-Oauth2/issues
- Documentation: README_LLAVEMX.rst
- Llave MX: https://www.gob.mx/llavemx
