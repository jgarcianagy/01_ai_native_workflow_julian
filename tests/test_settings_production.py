"""
Tests for config/settings_production.py (issue #16).

These run the settings module in a *subprocess*, not via a plain import in
this process, for two reasons:

1. `environ.Env` reads `os.environ` (and `.env`) at import time, and Django's
   settings are configured once per process. `uv run pytest` already runs
   with `DJANGO_SETTINGS_MODULE=config.settings_test` (see pyproject.toml),
   so importing `config.settings_production` here directly would either be a
   no-op (Django settings already configured) or would permanently mutate
   this test process's settings for every other test in the suite.
2. `config/settings.py` calls `environ.Env.read_env(BASE_DIR / '.env')`,
   which would load this repo's local, untracked `.env` file (which has a
   working `DJANGO_SECRET_KEY`) and mask the exact "missing env var" failure
   mode this issue is about. Each subprocess neutralizes `read_env` so the
   check reflects only the environment variables the subprocess is actually
   given, not whatever happens to be in a developer's local `.env` file.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Imports config.settings_production with django.setup(), after neutralizing
# django-environ's .env file loading (see module docstring above). Always
# exits 0; prints a distinct sentinel depending on which way it went, so the
# test can assert on stdout rather than on subprocess exit codes/tracebacks.
_CHECK_SCRIPT = """
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_production"

import environ
environ.Env.read_env = classmethod(lambda cls, *a, **k: None)

import django
from django.core.exceptions import ImproperlyConfigured

try:
    django.setup()
except ImproperlyConfigured as exc:
    print("IMPROPERLY_CONFIGURED:", exc)
else:
    from django.conf import settings
    print("DEBUG=", settings.DEBUG)
    print("SECRET_KEY_SET=", bool(settings.SECRET_KEY))
"""


def _check_production_settings(**extra_env):
    """Run _CHECK_SCRIPT in a subprocess with a controlled environment.

    The subprocess env is built from scratch (not copied from os.environ) so
    the test's own environment/shell can't accidentally supply
    DJANGO_SECRET_KEY and mask what's being tested.
    """
    import os

    env = {"PATH": os.environ.get("PATH", "")}
    env.update(extra_env)

    return subprocess.run(
        [sys.executable, "-c", _CHECK_SCRIPT],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_debug_is_hardcoded_false_when_secret_key_is_set():
    result = _check_production_settings(DJANGO_SECRET_KEY="a-real-production-secret")

    assert result.returncode == 0, result.stderr
    assert "IMPROPERLY_CONFIGURED" not in result.stdout
    assert "DEBUG= False" in result.stdout
    assert "SECRET_KEY_SET= True" in result.stdout


def test_debug_stays_false_even_if_debug_env_var_says_true():
    # DEBUG is hardcoded in config/settings_production.py, not env-driven,
    # so setting DEBUG=True in the environment must have no effect there.
    result = _check_production_settings(
        DJANGO_SECRET_KEY="a-real-production-secret",
        DEBUG="True",
    )

    assert result.returncode == 0, result.stderr
    assert "DEBUG= False" in result.stdout


def test_missing_secret_key_raises_improperly_configured():
    # No DJANGO_SECRET_KEY in the environment at all -- config/settings.py's
    # insecure dev fallback must NOT be used under settings_production.
    result = _check_production_settings()

    assert result.returncode == 0, result.stderr
    assert "IMPROPERLY_CONFIGURED" in result.stdout
    assert "DJANGO_SECRET_KEY" in result.stdout
    assert "DEBUG=" not in result.stdout
