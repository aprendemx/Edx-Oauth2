# LlaveMX OAuth2 backend for Open edX

Minimal python-social-auth backend for authenticating Open edX (Tutor) against LlaveMX. Ships only the backend class and an optional pipeline helper to associate users by CURP.

## Installation (Tutor)

1. Build and install the package inside your Tutor environment:
   ```bash
   pip install oauth2-llavemx
   ```
2. Add the backend and pipeline entry in `lms.env.json`:
   ```json
   {
     "SOCIAL_AUTH_BACKEND_PREFIX": "social_core.backends",
     "SOCIAL_AUTH_AUTHENTICATION_BACKENDS": [
       "oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2"
     ],
     "SOCIAL_AUTH_PIPELINE": [
       "social_core.pipeline.social_auth.social_details",
       "social_core.pipeline.social_auth.social_uid",
       "social_core.pipeline.social_auth.auth_allowed",
       "social_core.pipeline.social_auth.social_user",
       "oauth2_llavemx.pipeline.associate_by_curp",
       "social_core.pipeline.user.get_username",
       "social_core.pipeline.social_auth.associate_by_email",
       "social_core.pipeline.user.create_user",
       "social_core.pipeline.social_auth.associate_user",
       "social_core.pipeline.social_auth.load_extra_data",
       "social_core.pipeline.user.user_details"
     ]
   }
   ```
3. Configure LlaveMX credentials and WS basic-auth users:
   ```json
   {
     "SOCIAL_AUTH_LLAVEMX_KEY": "client_id",
     "SOCIAL_AUTH_LLAVEMX_SECRET": "client_secret",
     "SOCIAL_AUTH_LLAVEMX_WS_USER": "usuario_ws",
     "SOCIAL_AUTH_LLAVEMX_WS_PASSWORD": "password_ws"
   }
   ```

## Pipeline helper

`oauth2_llavemx.pipeline.associate_by_curp` links incoming LlaveMX accounts to existing Open edX users when CURP or email matches. It expects `custom_reg_form.ExtraInfo` to hold a `curp` field pointing to the user via a OneToOne relation.

## License

MIT License. See `LICENSE`.
