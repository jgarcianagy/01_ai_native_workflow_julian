# Hotel Maintenance Tracker

A tight, no-frills internal tool for a hotel's maintenance workflow. Full product
scope lives in `_docs/plan.md`; the v1 build backlog lives in `_docs/tasks.md`.
Read both before making product decisions — this file is a summary, not the
source of truth.

## Documents
- `_docs/process.md` - how work is organized

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

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

## Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking.
