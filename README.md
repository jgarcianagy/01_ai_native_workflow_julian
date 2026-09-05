# Hotel Maintenance Tracker

A tight, no-frills internal tool for a hotel's maintenance workflow (Django +
Postgres monolith). See `_docs/plan.md` for full product scope.

## Prerequisites

Before you start, make sure you have:

- **Docker Desktop** (or Docker Engine + Compose) — used to run a local
  Postgres 16 instance via `docker-compose.yml`
- **[uv](https://docs.astral.sh/uv/)** — used to manage the Python virtual
  environment and dependencies
- **Python 3.12+** — the version pinned in `pyproject.toml`
  (`requires-python = ">=3.12"`); `uv` will provision this for you if you
  don't already have it

## Getting started (clean clone to running dev server)

Run these commands in order from the repo root:

```bash
# 1. Install Python dependencies into .venv
uv sync

# 2. Create your local env file from the template
cp .env.example .env

# 3. Start local Postgres in the background
docker compose up -d

# 4. Apply database migrations
uv run python manage.py migrate

# 5. Run the dev server
uv run python manage.py runserver
```

The app will be available at `http://localhost:8000/`.

`.env` is your local, untracked copy of environment variables (`.gitignore`
excludes it) — edit it if you need non-default values. `.env.example`
documents every variable `config/settings.py` reads: `DJANGO_SECRET_KEY`,
`DEBUG`, `ALLOWED_HOSTS`, and the `DB_NAME` / `DB_USER` / `DB_PASSWORD` /
`DB_HOST` / `DB_PORT` values, which match the `db` service's defaults in
`docker-compose.yml` (Postgres 16, exposed on `localhost:5432`).

## Running tests

```bash
uv run pytest          # whole suite
uv run pytest tests/test_home.py   # one test file
```

`uv run pytest` runs against **SQLite**, not the Postgres container — see
`config/settings_test.py`, which is only used by the test suite. This means
`uv run pytest` will pass even if Docker/Postgres isn't running. The dev
server and `manage.py migrate` always use the real Postgres config in
`config/settings.py`.

## Other useful commands

- `uv run python manage.py makemigrations` — after changing models
- `uv run python manage.py createsuperuser` — admin access (for seeding
  `Technician` data, etc.)
- `docker compose down` — stop local Postgres
