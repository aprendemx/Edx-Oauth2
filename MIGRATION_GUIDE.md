# Migration Guide: NEM OAuth2 → Llave MX OAuth2

## Overview

This guide helps you migrate from `oauth2_nem` to the new `oauth2_llavemx` backend.

## What Changed?

### Package Name
- **Old:** `edx-oauth2-nem` / `oauth2_nem`
- **New:** `edx-oauth2-llavemx` / `oauth2_llavemx`

### Backend Class Name
- **Old:** `oauth2_nem.nem_oauth.NEMOpenEdxOAuth2`
- **New:** `oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2`

### Backend Identifier
- **Old:** `name = "nem-oauth"`
- **New:** `name = "llavemx"`

### Major Features Added
- ✅ OAuth 2.0 + PKCE (mandatory)
- ✅ Custom JSON POST for token exchange
- ✅ Better error handling
- ✅ Role management support
- ✅ SSO logout implementation
- ✅ Comprehensive test suite

## Migration Steps

### 1. Update Requirements

**Option A: Replace in requirements.txt**
```diff
- edx-oauth2-nem==1.0.22
+ edx-oauth2-llavemx>=2.0.0
```

**Option B: Install alongside (temporary)**
```text
edx-oauth2-nem==1.0.22  # Keep temporarily
edx-oauth2-llavemx>=2.0.0
```

### 2. Update Django Settings

```python
# settings.py or lms.env.json

INSTALLED_APPS = [
    # ... other apps
-   'oauth2_nem',
+   'oauth2_llavemx',
]

AUTHENTICATION_BACKENDS = [
-   'oauth2_nem.nem_oauth.NEMOpenEdxOAuth2',
+   'oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2',
    # ... other backends
]

# Update configuration keys
- SOCIAL_AUTH_NEM_OAUTH_KEY = 'your_client_id'
+ SOCIAL_AUTH_LLAVEMX_KEY = 'your_client_id'

- SOCIAL_AUTH_NEM_OAUTH_SECRET = 'your_secret'
+ SOCIAL_AUTH_LLAVEMX_SECRET = 'your_secret'
```

### 3. Update Tutor Configuration

```bash
# Remove old backend
tutor config save --unset THIRD_PARTY_AUTH_BACKENDS

# Add new backend
tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS="edx-oauth2-llavemx>=2.0.0"
tutor config save --append ADDL_INSTALLED_APPS="oauth2_llavemx"
tutor config save --append THIRD_PARTY_AUTH_BACKENDS="oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"

# Rebuild
tutor images build openedx
tutor local restart
```

### 4. Update Third-Party Auth Configuration

In Django Admin (`/admin/`):

1. Go to **Third Party Authentication > Provider Configuration (OAuth)**
2. Find your NEM OAuth provider
3. Update:
   - **Backend name:** `nem-oauth` → `llavemx`
   - **Name:** "Nueva Escuela Mexicana" → "Llave MX"
4. Or create a new provider and disable the old one

### 5. Database Migration (User Social Auth)

Existing users have `UserSocialAuth` records with `provider='nem-oauth'`.

**Option A: Update in Database (Recommended)**

```sql
-- Backup first!
-- Update provider name in user social auth
UPDATE social_auth_usersocialauth 
SET provider = 'llavemx' 
WHERE provider = 'nem-oauth';
```

**Option B: Support Both (Temporary)**

Keep both backends active temporarily:

```python
AUTHENTICATION_BACKENDS = [
    'oauth2_nem.nem_oauth.NEMOpenEdxOAuth2',  # Old users
    'oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2',  # New users
]
```

### 6. Update URLs (if custom)

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # Old
-   path('auth/', include('social_django.urls', namespace='social')),
    
    # New (no change needed if using default)
+   path('auth/', include('social_django.urls', namespace='social')),
]
```

Login URLs change automatically:
- **Old:** `/login/nem-oauth/`
- **New:** `/login/llavemx/`

### 7. Update Templates (if custom)

```html
<!-- Old -->
<a href="{% url 'social:begin' 'nem-oauth' %}">
  Login with NEM
</a>

<!-- New -->
<a href="{% url 'social:begin' 'llavemx' %}">
  Login with Llave MX
</a>
```

### 8. Test Migration

1. **Create test user** with new backend
2. **Verify existing users** can still log in
3. **Check user data sync** on login
4. **Test error scenarios** (expired token, invalid code)
5. **Verify logging** works correctly

### 9. Update Llave MX Registration

If endpoints changed, update your app registration at:
https://val-llavemxintegracion.infotec.mx

Update redirect URLs:
```diff
- https://yourdomain.gob.mx/auth/complete/nem-oauth/
+ https://yourdomain.gob.mx/auth/complete/llavemx/
```

## Backward Compatibility

The `oauth2_nem` package now includes a deprecation warning and can import from `oauth2_llavemx` for compatibility:

```python
# This still works but shows a warning
from oauth2_nem.nem_oauth import NEMOpenEdxOAuth2

# DeprecationWarning: oauth2_nem is deprecated...
```

## Breaking Changes

### 1. Endpoints
- Updated to official Llave MX API endpoints
- Production vs VAL environment support

### 2. PKCE Required
- All auth flows now use PKCE
- code_verifier/code_challenge automatically generated

### 3. Token Exchange
- Now uses POST with JSON body
- Custom request format for Llave MX

### 4. Username Field
- Explicitly uses CURP (was using email before)
- More reliable for government systems

## Rollback Plan

If you need to rollback:

```bash
# 1. Keep old package in requirements
pip install edx-oauth2-nem==1.0.22

# 2. Revert settings
AUTHENTICATION_BACKENDS = [
    'oauth2_nem.nem_oauth.NEMOpenEdxOAuth2',
]

# 3. Revert provider in Django Admin
Backend name: llavemx → nem-oauth

# 4. Revert database (if updated)
UPDATE social_auth_usersocialauth 
SET provider = 'nem-oauth' 
WHERE provider = 'llavemx';
```

## Timeline Recommendation

### Week 1: Preparation
- ✅ Review migration guide
- ✅ Test in development environment
- ✅ Update Llave MX registration

### Week 2: Staging Deployment
- ✅ Deploy to staging
- ✅ Run both backends in parallel
- ✅ Test user flows
- ✅ Verify logging

### Week 3: Production Migration
- ✅ Schedule maintenance window
- ✅ Backup database
- ✅ Deploy new backend
- ✅ Update database records
- ✅ Monitor for issues

### Week 4: Cleanup
- ✅ Remove old backend (if stable)
- ✅ Update documentation
- ✅ Train support team

## Support

- **Issues:** https://github.com/aprendemx/Edx-Oauth2/issues
- **Documentation:** See README_LLAVEMX.rst
- **Llave MX:** https://www.gob.mx/llavemx

## Checklist

- [ ] Requirements updated
- [ ] Django settings updated
- [ ] Tutor configuration updated (if applicable)
- [ ] Third-party auth provider updated in admin
- [ ] Database migration completed
- [ ] Templates updated (if custom)
- [ ] Llave MX registration updated
- [ ] Testing completed
- [ ] Documentation updated
- [ ] Team trained
- [ ] Monitoring in place
- [ ] Rollback plan ready
