"""
Validates .github/workflows/ci.yml (issue #17).

Issue #17 explicitly forbids adding a new pyproject.toml dependency ("No new
pyproject.toml dependency ... Do not add one without asking", per CLAUDE.md),
and PyYAML is not installed in this project's uv-managed environment. So this
test validates the workflow in two complementary ways:

1. "Parses cleanly": it looks for a python interpreter on PATH that is *not*
   this project's venv interpreter and that happens to have PyYAML available
   (GitHub Actions' `ubuntu-latest` runners ship PyYAML in their system
   Python, e.g. for cloud-init tooling, so this runs for real in CI). If no
   such interpreter can be found anywhere, that one assertion is skipped with
   a clear reason -- every other assertion below still runs regardless, since
   they only need the raw text.
2. Every other acceptance criterion from issue #17 is checked with direct
   text/regex assertions against the raw workflow file. These never depend on
   PyYAML being available anywhere and always run, in every environment.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def workflow_text():
    assert WORKFLOW_PATH.exists(), f"expected a workflow file at {WORKFLOW_PATH}"
    return WORKFLOW_PATH.read_text()


def _external_yaml_capable_python():
    """Find a python interpreter, other than this project's uv venv, that
    has PyYAML installed -- without this project depending on PyYAML.

    `uv run pytest` prepends this project's `.venv/bin` to PATH, so a plain
    `shutil.which("python3")` would just resolve back to this same venv
    interpreter. Search PATH with that one directory excluded instead, so
    this finds the *next* python3/python on PATH (e.g. system Python, or a
    Python.framework install) -- exactly the kind of interpreter that
    GitHub Actions' `ubuntu-latest` runners ship PyYAML in already, for
    tooling like cloud-init.
    """
    # Exclude both the project's `.venv/bin` (which `uv run` prepends to
    # PATH) and, since it's often a symlink farm, the real resolved
    # directory `sys.executable` lives in too.
    excluded_bins = {
        (REPO_ROOT / ".venv" / "bin").resolve(),
        Path(sys.executable).resolve().parent,
    }
    search_dirs = [
        d
        for d in os.environ.get("PATH", "").split(os.pathsep)
        if d and Path(d).resolve() not in excluded_bins
    ]
    search_path = os.pathsep.join(search_dirs)

    seen = set()
    for name in ("python3", "python"):
        path = shutil.which(name, path=search_path)
        if not path or path == sys.executable or path in seen:
            continue
        seen.add(path)
        probe = subprocess.run(
            [path, "-c", "import yaml"], capture_output=True, timeout=10
        )
        if probe.returncode == 0:
            return path
    return None


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists()


def test_workflow_parses_as_valid_yaml():
    interpreter = _external_yaml_capable_python()
    if interpreter is None:
        pytest.skip(
            "no python interpreter with PyYAML found on PATH; skipping the "
            "real parse (adding PyYAML as a project dependency is out of "
            "scope for issue #17). The structural checks in this file's "
            "other tests still run and do not depend on this."
        )
    script = "import sys, yaml\nyaml.safe_load(open(sys.argv[1]))\nprint('OK')\n"
    result = subprocess.run(
        [interpreter, "-c", script, str(WORKFLOW_PATH)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_has_name_and_job(workflow_text):
    assert re.search(r"(?m)^name:\s*\S", workflow_text)
    assert re.search(r"(?m)^jobs:\s*$", workflow_text)
    assert re.search(r"(?m)^\s{2}test:\s*$", workflow_text)


def test_triggers_on_push_and_pull_request_to_main(workflow_text):
    assert re.search(r"push:\s*\n\s*branches:\s*\[main\]", workflow_text)
    assert re.search(r"pull_request:\s*\n\s*branches:\s*\[main\]", workflow_text)


def test_checks_out_repo(workflow_text):
    assert "actions/checkout@" in workflow_text


def test_sets_up_python_3_12(workflow_text):
    assert "actions/setup-python@" in workflow_text
    assert re.search(r"python-version:\s*[\"']?3\.12[\"']?", workflow_text)


def test_installs_uv_action(workflow_text):
    assert "astral-sh/setup-uv@" in workflow_text


def test_uv_sync_includes_dev_group(workflow_text):
    assert re.search(r"uv sync\b.*--group\s+dev", workflow_text)


def test_postgres_service_matches_docker_compose(workflow_text):
    compose_text = COMPOSE_PATH.read_text()
    # Sanity-check the fixture this test compares against.
    assert "postgres:16" in compose_text
    assert "POSTGRES_DB: hotel_maintenance" in compose_text
    assert "POSTGRES_USER: hotel_maintenance" in compose_text
    assert "POSTGRES_PASSWORD: hotel_maintenance" in compose_text

    assert "image: postgres:16" in workflow_text
    assert "POSTGRES_DB: hotel_maintenance" in workflow_text
    assert "POSTGRES_USER: hotel_maintenance" in workflow_text
    assert "POSTGRES_PASSWORD: hotel_maintenance" in workflow_text
    assert re.search(r"-\s*5432:5432", workflow_text)


def test_postgres_health_check_present(workflow_text):
    assert "pg_isready" in workflow_text


def test_migrate_step_present(workflow_text):
    assert "manage.py migrate" in workflow_text


def test_pytest_step_overrides_settings_module_to_postgres(workflow_text):
    # The pytest step must override to config.settings (Postgres). A comment
    # elsewhere in the file is allowed to mention config.settings_test (e.g.
    # explaining *why* the override exists) -- only an actual env/setting
    # assignment to it would be wrong, so check line-by-line and ignore
    # comment lines.
    assert "DJANGO_SETTINGS_MODULE: config.settings" in workflow_text
    assert "uv run pytest" in workflow_text
    for line in workflow_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "config.settings_test" not in stripped, (
            f"non-comment line assigns/references config.settings_test: {line!r}"
        )


def test_db_env_vars_match_service_credentials(workflow_text):
    for line in (
        "DB_NAME: hotel_maintenance",
        "DB_USER: hotel_maintenance",
        "DB_PASSWORD: hotel_maintenance",
        "DB_HOST: localhost",
        "DB_PORT: 5432",
    ):
        assert line in workflow_text


def test_django_secret_key_is_set(workflow_text):
    assert re.search(r"(?m)^\s*DJANGO_SECRET_KEY:\s*\S", workflow_text)


def test_pyproject_settings_test_default_untouched():
    pyproject_text = PYPROJECT_PATH.read_text()
    assert 'DJANGO_SETTINGS_MODULE = "config.settings_test"' in pyproject_text


def test_no_swallowed_failures(workflow_text):
    assert "continue-on-error" not in workflow_text
    assert "|| true" not in workflow_text
    assert "exit 0" not in workflow_text
