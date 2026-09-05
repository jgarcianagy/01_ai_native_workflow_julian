"""
Settings for `uv run pytest` only.

This sandbox has no local Postgres/Docker available, so tests run against
SQLite instead. `config.settings` (used by runserver/migrate/production)
is untouched and still targets Postgres.
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}
