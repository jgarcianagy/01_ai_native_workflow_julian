import datetime

import pytest
from django.core.management import call_command
from django.utils import timezone

from maintenance.models import MaintenanceTask, RecurrenceRule


def make_rule(**overrides):
    defaults = {
        "title": "Replace HVAC filters",
        "description": "Replace air filters in all guest room HVAC units.",
        "location": "All Guest Rooms",
        "priority": MaintenanceTask.Priority.NORMAL,
        "interval_days": 90,
    }
    defaults.update(overrides)
    return RecurrenceRule.objects.create(**defaults)


@pytest.mark.django_db
def test_never_generated_rule_creates_a_task():
    rule = make_rule(last_generated_date=None)

    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() == 1
    task = MaintenanceTask.objects.get()
    assert task.title == rule.title
    assert task.description == rule.description
    assert task.location == rule.location
    assert task.status == MaintenanceTask.Status.OPEN
    assert task.technician is None
    assert not task.issue_photo
    assert not task.completion_photo


@pytest.mark.django_db
def test_due_rule_creates_a_task_and_updates_last_generated_date():
    today = timezone.localdate()
    rule = make_rule(
        interval_days=30,
        last_generated_date=today - datetime.timedelta(days=30),
    )

    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() == 1
    rule.refresh_from_db()
    assert rule.last_generated_date == today


@pytest.mark.django_db
def test_rule_overdue_by_multiple_intervals_generates_exactly_one_task():
    today = timezone.localdate()
    rule = make_rule(
        interval_days=7,
        last_generated_date=today - datetime.timedelta(days=100),
    )

    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() == 1
    rule.refresh_from_db()
    assert rule.last_generated_date == today


@pytest.mark.django_db
def test_not_yet_due_rule_creates_no_task():
    today = timezone.localdate()
    rule = make_rule(
        interval_days=30,
        last_generated_date=today - datetime.timedelta(days=1),
    )

    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() == 0
    rule.refresh_from_db()
    assert rule.last_generated_date == today - datetime.timedelta(days=1)


@pytest.mark.django_db
def test_running_twice_same_day_does_not_duplicate():
    make_rule(last_generated_date=None)

    call_command("generate_recurring_tasks")
    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() == 1


@pytest.mark.django_db
def test_created_task_priority_copied_from_rule():
    make_rule(priority=MaintenanceTask.Priority.URGENT, last_generated_date=None)

    call_command("generate_recurring_tasks")

    task = MaintenanceTask.objects.get()
    assert task.priority == MaintenanceTask.Priority.URGENT


@pytest.mark.django_db
def test_zero_rules_succeeds_and_creates_nothing():
    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() == 0


@pytest.mark.django_db
def test_prints_summary_line(capsys):
    make_rule(last_generated_date=None)
    make_rule(
        title="Test smoke detectors",
        description="Test smoke detectors on every floor.",
        location="All Floors",
        priority=MaintenanceTask.Priority.URGENT,
        interval_days=30,
        last_generated_date=None,
    )

    call_command("generate_recurring_tasks")

    captured = capsys.readouterr()
    assert "Created 2 task(s)." in captured.out
