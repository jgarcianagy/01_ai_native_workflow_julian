# Hotel Maintenance Tracker

A tight, no-frills internal tool for a hotel's maintenance workflow. Full product
scope lives in `_docs/plan.md`; the v1 build backlog lives in `_docs/tasks.md`.
Read both before making product decisions — this file is a summary, not the
source of truth.

## Documents
- `_docs/process.md` - how work is organized
- `_docs/task-template.md` - template used to groom a task before implementation
- `_docs/team/pm.md` - PM role: grooms tasks into the template before anyone implements them

## Stack

Django + Postgres monolith.

## Product Scope (v1)

- Shared desktop dashboard, no login/accounts/roles. Staff pick their name per task.
- Only front desk/management can create tasks (staff report issues to them verbally/in person).
- Task fields (all required): title, description, issue photo, completion photo,
  status (Open / In Progress / Done), priority (Urgent / Normal / Low), location.
- Manager manually assigns each task to a technician — no self-claiming, no auto-assignment.
- A task can only move to Done if a completion photo is attached.
- Recurring/preventive maintenance: fixed-interval only (e.g. every 7/30/90 days),
  auto-creates a new task when due. No calendar-date scheduling in v1.
- No notifications, no reporting/history/analytics. Dashboard shows current tasks only.

Explicitly deferred to v2: mobile access, user accounts/login, notifications,
historical reporting, calendar-date recurrence, external contractors.

## Commands

Setup (first time, or after pulling changes to `docker-compose.yml`/`pyproject.toml`):
- `uv sync` - install dependencies into `.venv`
- `cp .env.example .env` - local env vars (DB credentials, secret key); edit if needed
- `docker compose up -d` - start local Postgres (see `docker-compose.yml`)
- `uv run python manage.py migrate` - apply migrations

Day to day:
- `uv run python manage.py runserver` - run the dev server
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file
- `uv run python manage.py makemigrations` - after changing models
- `uv run python manage.py createsuperuser` - admin access (for seeding `Technician` data, etc.)
- `docker compose down` - stop local Postgres

## Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking.
