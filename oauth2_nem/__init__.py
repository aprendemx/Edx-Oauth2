"""
OAuth2 backend for Nueva Escuela Mexicana

DEPRECATED: This package has been superseded by oauth2_llavemx.
Please migrate to the new package for Llave MX integration.

This module now provides compatibility imports that point to oauth2_llavemx.
"""
import warnings

# Issue deprecation warning
warnings.warn(
    "oauth2_nem is deprecated and will be removed in a future version. "
    "Please migrate to oauth2_llavemx for Llave MX integration. "
    "See README_LLAVEMX.rst for migration instructions.",
    DeprecationWarning,
    stacklevel=2
)

# Compatibility import - redirect to new package
try:
    from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2 as NEMOpenEdxOAuth2
    __all__ = ["NEMOpenEdxOAuth2"]
except ImportError:
    # If oauth2_llavemx is not installed, keep original implementation
    from oauth2_nem.nem_oauth import NEMOpenEdxOAuth2
    __all__ = ["NEMOpenEdxOAuth2"]
