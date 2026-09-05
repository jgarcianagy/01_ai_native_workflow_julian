# Hotel Maintenance Tracker — Backlog (v1)

Stack: Django + Postgres monolith (see `_docs/plan.md` for product scope).

## 1. Project scaffold with a passing test
Goal: Get an empty, working Django project committed with CI-able tests green.
Description: Create a new Django project and a single app (e.g. `maintenance`). Wire up Postgres as the database backend in settings (local dev config only). Add one trivial test (e.g. a homepage view returns 200, or a smoke test) and confirm `manage.py test` passes.

## 2. Local dev environment & Postgres setup
Goal: Anyone can clone the repo and run the app locally against Postgres with one documented command sequence.
Description: Add a `requirements.txt` (or `pyproject.toml`), environment variable handling for DB credentials (e.g. via `django-environ` or `.env`), and a README section with setup steps. Include a way to spin up Postgres locally (docker-compose is fine) so the DB isn't assumed to be pre-installed.

## 3. Technician model
Goal: Store the list of in-house maintenance technicians staff can pick from.
Description: Add a `Technician` model with at minimum a name field. Register it in Django admin so management can add/remove technicians without a custom UI. No login/roles — admin access is just for this seed data.

## 4. MaintenanceTask model
Goal: Represent a single maintenance task with all v1-required fields.
Description: Add a `MaintenanceTask` model with: title, description, location (free text — room number or area), status (Open / In Progress / Done, default Open), priority (Urgent / Normal / Low), assigned technician (FK to `Technician`, nullable until assigned), and timestamps (created_at, updated_at). Leave photo fields and recurrence out of this task — later tasks add those.

## 5. Photo fields on MaintenanceTask
Goal: Support the "picture on creation" and "picture on completion" requirements.
Description: Add two image fields to `MaintenanceTask`: one for the initial issue photo (required at creation) and one for the completion photo (required only when marking a task Done). Configure `MEDIA_ROOT`/`MEDIA_URL` for local file storage. Don't build the enforcement logic yet — just the fields and storage config.

## 6. Enforce "Done requires completion photo" rule
Goal: A task cannot be set to Done without a completion photo attached.
Description: Add validation (model `clean()` and/or form-level validation) so that saving a `MaintenanceTask` with status=Done fails unless the completion photo field is populated. Add tests covering: valid Done with photo, invalid Done without photo, and non-Done statuses saving fine without a completion photo.

## 7. Task creation form
Goal: Front desk/management can log a new maintenance task.
Description: Build a Django form + view for creating a `MaintenanceTask`: title, description, location, priority, and the initial issue photo (required). Status defaults to Open and technician assignment is left blank at creation (assignment happens separately, see task 9). No authentication — this is a shared, unrestricted page per the plan.

## 8. Task list dashboard
Goal: One shared screen showing all current tasks grouped/filterable by status.
Description: Build a view + template listing all `MaintenanceTask` records, with a way to filter by status (Open / In Progress / Done) and see priority and location at a glance. This is the main screen staff will leave open on a shared desktop — no pagination assumptions beyond what's reasonable for a single hotel's task volume.

## 9. Task detail view + manual assignment
Goal: Let a manager assign a technician to an existing task and view full task details.
Description: Build a detail view for a single `MaintenanceTask` showing all fields and photos. Add a way to set/change the assigned technician from a dropdown of existing `Technician` records. No self-claiming — assignment is a manual field update, not tied to any logged-in identity.

## 10. Status update + completion photo upload flow
Goal: Let staff move a task through Open → In Progress → Done, with the Done transition requiring a completion photo upload.
Description: Build the UI flow for changing a task's status from the detail view. When changing to Done, require uploading the completion photo as part of the same action (reuse validation from task 6). Confirm the form surfaces a clear error if someone tries to mark Done without a photo.

## 11. RecurrenceRule model
Goal: Store fixed-interval preventive maintenance schedules.
Description: Add a `RecurrenceRule` model (or fields on `MaintenanceTask`) capturing: interval in days (e.g. 7/30/90), the location/title/description template for tasks it generates, and the last-generated date. Keep this separate from the reactive `MaintenanceTask` creation flow in task 7.

## 12. Recurring task auto-creation command
Goal: Automatically create a new `MaintenanceTask` when a recurrence interval comes due.
Description: Write a Django management command that checks all `RecurrenceRule` records, and for any where `last_generated_date + interval_days <= today`, creates a new open `MaintenanceTask` (unassigned, Open status, no photo yet) and updates `last_generated_date`. Add tests covering "due" and "not yet due" cases.

## 13. Schedule the recurring task command
Goal: The recurring-task check runs automatically every day without manual intervention.
Description: Wire up a scheduler (e.g. system cron calling `manage.py <command>`, or `django-crontab`/`APScheduler` if a cron-less approach is preferred) to run the task-12 management command daily. Document how to configure/verify it's running in the deployment environment.

## 14. Seed data for local development
Goal: A fresh dev environment can be populated with realistic sample data in one command.
Description: Add a management command or fixture that creates a handful of sample technicians, a few open/in-progress/done tasks with placeholder photos, and one or two recurrence rules — enough to exercise the dashboard without manually clicking through forms.

## 15. Dashboard styling for shared desktop display
Goal: The dashboard is easy to read at a glance on a shared front-desk screen.
Description: Add basic CSS to the list view so status and priority are visually distinguishable (e.g. color-coded badges), the layout suits a desktop browser window left open all day, and there's no login screen or unrelated navigation cluttering the view.

## 16. Production deployment config
Goal: The app can be deployed to run continuously for the hotel, serving media files correctly.
Description: Add production settings (DEBUG=False, ALLOWED_HOSTS, secret key from env, static/media file serving via whitenoise or an object store), and document the deployment steps for whatever host is chosen (e.g. a small VM or PaaS). Confirm uploaded photos persist across deploys.
