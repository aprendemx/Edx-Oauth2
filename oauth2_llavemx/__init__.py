"""
OAuth2 backend for Llave MX - Mexican Government Digital Identity Platform
"""
from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

__all__ = ["LlaveMXOAuth2"]
default_app_config = "oauth2_llavemx.apps.OAuth2LlaveMXConfig"
