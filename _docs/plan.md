# Hotel Maintenance Tracker — v1 Scope

## Access
- Shared desktop dashboard, no login required
- Staff pick their name per task (no accounts, no roles/permissions)

## Task Creation
- Only front desk / management can create tasks
- Staff report issues to front desk/management, who log them in the system

## Task Fields (all required)
- Title
- Description
- Picture 
- Picture when task done
- Status: Open / In Progress / Done
- Priority: Urgent / Normal / Low
- Location: Room number / area

## Assignment
- Manager manually assigns each task to a specific technician
- No self-claiming or auto-assignment in v1
- Status Done only with picture task done uploaded

## Execution Team
- In-house maintenance team (multiple technicians)

## Recurring / Preventive Maintenance
- Supported alongside reactive (break-fix) tasks
- Fixed-interval scheduling (e.g. every 7 / 30 / 90 days)
- New task auto-created when interval is due
- No specific calendar-date scheduling in v1

## Notifications
- None — staff and managers check the dashboard directly
- No email or push notifications

## Reporting
- None in v1
- Dashboard shows only current tasks by status (Open / In Progress / Done)
- No history, no analytics, no charts

---

## Summary
A tight, no-frills tool: one shared desktop screen, controlled task entry (front desk/management only), manual assignment to technicians, and basic fixed-interval recurring maintenance. Deliberately excludes mobile access, logins/roles, notifications, and reporting for v1.

## Natural v2 Additions
- Mobile-friendly access for technicians
- User accounts / login (with or without roles)
- Notifications (email to technician on assignment, to manager on completion)
- Historical reporting (completion times, frequency by room/area, filters & charts)
- Calendar-date-based recurring schedules
- Support for external contractors alongside in-house staff