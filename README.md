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

# 4b. (Optional) Populate local dev data — DESTRUCTIVE, see warning below
uv run python manage.py seed_data

# 5. Run the dev server
uv run python manage.py runserver
```

`manage.py seed_data` is optional and for local development only. **It is
destructive**: it deletes all existing `Technician`, `MaintenanceTask`, and
`RecurrenceRule` rows before recreating a fixed seed set (a handful of
technicians, tasks covering every status/priority/assignment combination,
and a recurrence rule), so you can open the dashboard immediately without
creating data by hand. Never run it against a production database.

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

## Production settings

`config/settings_production.py` exists so this app cannot accidentally run
with development defaults in a production-like environment. It follows the
same override pattern as `config/settings_test.py`: `from .settings import *`,
then overrides only what production needs.

To point Django at it, set:

```
DJANGO_SETTINGS_MODULE=config.settings_production
```

Under that module:

- `DEBUG` is hardcoded to `False` — it is not read from the environment
  there, so no env var can re-enable it.
- `SECRET_KEY` is read via `env('DJANGO_SECRET_KEY')` with **no default**.
  Unlike `config/settings.py` (which falls back to an insecure hardcoded dev
  key), a production deployment must set `DJANGO_SECRET_KEY` explicitly, or
  Django raises `ImproperlyConfigured` at startup instead of silently using
  an insecure key.
- `ALLOWED_HOSTS` likewise has no working default for production use — set
  it explicitly to the real domain(s)/host(s) the deployment is served from.

`.env.production.example` documents every env var this settings module
requires or reads (`DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, and the `DB_*`
values) with placeholder, non-functional values — it is intentionally
distinct from the dev-oriented `.env.example`.

**This settings module only covers Django's own settings.** It does not make
the app deployable end-to-end. Still unresolved, and tracked in
[#20](https://github.com/juliangarcianagyabi/01_ai_native_workflow_julian/issues/20)
(which requires dependency sign-off first, per this repo's rule on adding
`pyproject.toml` dependencies):

- A production WSGI server (e.g. gunicorn).
- Production static-file serving (e.g. whitenoise).
- A containerized `web` service / `Dockerfile` (today `docker-compose.yml`
  only defines the `db` service).
- The exact containerized invocation of the recurring-task cron command
  (see "Scheduling the recurring task command" below).
- Media (uploaded photo) persistence across redeploys/restarts.

## Scheduling the recurring task command

`manage.py generate_recurring_tasks` (see `maintenance/management/commands/generate_recurring_tasks.py`)
needs to run once a day so recurring/preventive maintenance tasks get created
automatically instead of relying on someone to trigger it by hand. This is
done with a plain OS-level cron entry (a systemd timer works equally well as
an alternative) — **no new Python dependency is added for this**.
`django-crontab`, Celery (+ beat), and `APScheduler` were all considered and
rejected for v1 because each would require adding a new `pyproject.toml`
dependency, which per this repo's rule ("Dependencies are added in
`pyproject.toml`. Do not add one without asking") needs sign-off first. If
plain cron turns out to be insufficient for the eventual deployment target
(e.g. a host with no cron access), that's a new issue to open and get
sign-off on — not something to fold in here.

For a bare-host deployment, the crontab line is:

```
0 3 * * * cd /path/to/app && uv run python manage.py generate_recurring_tasks >> /var/log/hotel-maintenance/recurring-tasks.log 2>&1
```

This runs the exact same command documented above and elsewhere in this
README — `uv run python manage.py generate_recurring_tasks` — with no extra
flags, so there's no drift between what's documented and what cron actually
invokes.

`docker-compose.yml` today only defines a `db` service; there is no `web`/
`app` service to run this against yet (that's a separate deployment/
production-setup concern). So this doc intentionally does not invent a
`docker compose run web ...` line against a service that doesn't exist. The
exact containerized invocation (service name, working directory, log path)
depends on that future production setup and should be reconciled once it
lands — until then, the command above is the one to run, whether by hand,
via host cron, or adapted into whatever process manager the eventual
container setup uses.

**Verifying the job ran**, without any new logging/notification
infrastructure:

- Check the log file the cron line redirects to
  (`/var/log/hotel-maintenance/recurring-tasks.log` in the example above) for
  stdout/stderr, including the command's own `Created N task(s).` line.
- And/or spot-check that a `RecurrenceRule`'s `last_generated_date` advanced
  to today, e.g. via `uv run python manage.py shell`:

  ```python
  from maintenance.models import RecurrenceRule
  RecurrenceRule.objects.values_list("title", "last_generated_date")
  ```

**Overlapping and missed runs are already safe, with no new locking added
here:**

- Running the command twice on the same day (e.g. a manual run plus the
  scheduled one landing the same day) does not create duplicate tasks —
  `generate_recurring_tasks` is already idempotent per day, because it only
  creates a task for a rule when `last_generated_date` shows the rule is due,
  and immediately advances `last_generated_date` to today. This issue adds
  only the trigger (cron); it does not add any new mutex/locking, and none is
  needed.
- A missed run (e.g. the host is down overnight) is already tolerated: a rule
  simply stays due until the command next runs, and `last_generated_date` is
  set to today rather than incremented by the interval, so there's no
  duplicate backlog to catch up on. That catch-up-without-duplicating-history
  behavior belongs to `generate_recurring_tasks` itself, not to the
  scheduling mechanism documented here.
