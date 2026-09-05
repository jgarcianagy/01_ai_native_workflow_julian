"""
Settings for a production deployment (`DJANGO_SETTINGS_MODULE=config.settings_production`).

This sandbox has no Docker/Postgres available, so this module cannot be
exercised against a live production environment here — see issue #16.
Actually serving the app (WSGI server, static-file serving, a containerized
`web` service, and media persistence across redeploys) is tracked in #20,
which requires dependency sign-off first; this module only makes the
settings themselves production-safe.

Following the same override pattern as `config/settings_test.py`: import
everything from `config.settings` and override only what production needs.
"""

from .settings import *  # noqa: F401,F403

# SECURITY: hardcoded, not env-driven — no combination of missing/
# misconfigured env vars can start this settings module with debug on.
DEBUG = False

# SECURITY: no default. A missing DJANGO_SECRET_KEY raises
# django.core.exceptions.ImproperlyConfigured at startup instead of silently
# falling back to the insecure dev key in config/settings.py.
SECRET_KEY = env('DJANGO_SECRET_KEY')
