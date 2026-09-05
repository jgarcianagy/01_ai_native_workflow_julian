import datetime

import pytest
from django.core.management import call_command
from django.utils import timezone

from maintenance.models import MaintenanceTask, RecurrenceRule, Technician


@pytest.mark.django_db
def test_creates_at_least_three_technicians():
    call_command("seed_data")

    assert Technician.objects.count() >= 3


@pytest.mark.django_db
def test_tasks_cover_all_statuses_and_priorities():
    call_command("seed_data")

    statuses = set(MaintenanceTask.objects.values_list("status", flat=True))
    priorities = set(MaintenanceTask.objects.values_list("priority", flat=True))

    assert statuses == {
        MaintenanceTask.Status.OPEN,
        MaintenanceTask.Status.IN_PROGRESS,
        MaintenanceTask.Status.DONE,
    }
    assert priorities == {
        MaintenanceTask.Priority.URGENT,
        MaintenanceTask.Priority.NORMAL,
        MaintenanceTask.Priority.LOW,
    }


@pytest.mark.django_db
def test_tasks_include_assigned_and_unassigned():
    call_command("seed_data")

    assert MaintenanceTask.objects.filter(technician__isnull=False).exists()
    assert MaintenanceTask.objects.filter(technician__isnull=True).exists()


@pytest.mark.django_db
def test_every_task_has_a_real_issue_photo():
    call_command("seed_data")

    for task in MaintenanceTask.objects.all():
        assert task.issue_photo
        assert task.issue_photo.name


@pytest.mark.django_db
def test_done_tasks_have_completion_photo():
    call_command("seed_data")

    done_tasks = MaintenanceTask.objects.filter(status=MaintenanceTask.Status.DONE)
    assert done_tasks.exists()
    for task in done_tasks:
        assert task.completion_photo


@pytest.mark.django_db
def test_at_least_one_non_done_task_has_no_completion_photo():
    call_command("seed_data")

    non_done_without_photo = MaintenanceTask.objects.filter(
        completion_photo="",
    ).exclude(status=MaintenanceTask.Status.DONE)

    assert non_done_without_photo.exists()


@pytest.mark.django_db
def test_creates_at_least_one_overdue_recurrence_rule():
    call_command("seed_data")

    assert RecurrenceRule.objects.exists()

    today = timezone.localdate()
    overdue = [
        rule
        for rule in RecurrenceRule.objects.all()
        if rule.last_generated_date is None
        or rule.last_generated_date
        + datetime.timedelta(days=rule.interval_days)
        <= today
    ]
    assert overdue


@pytest.mark.django_db
def test_generate_recurring_tasks_creates_a_task_after_seeding():
    call_command("seed_data")
    count_before = MaintenanceTask.objects.count()

    call_command("generate_recurring_tasks")

    assert MaintenanceTask.objects.count() > count_before


@pytest.mark.django_db
def test_running_twice_does_not_accumulate_data():
    call_command("seed_data")
    technician_count = Technician.objects.count()
    task_count = MaintenanceTask.objects.count()
    rule_count = RecurrenceRule.objects.count()

    call_command("seed_data")

    assert Technician.objects.count() == technician_count
    assert MaintenanceTask.objects.count() == task_count
    assert RecurrenceRule.objects.count() == rule_count


@pytest.mark.django_db
def test_running_twice_clears_unrelated_manually_created_rows():
    Technician.objects.create(name="Manually Added Tech")

    call_command("seed_data")
    call_command("seed_data")

    assert not Technician.objects.filter(name="Manually Added Tech").exists()


@pytest.mark.django_db
def test_every_seeded_task_passes_full_clean():
    call_command("seed_data")

    for task in MaintenanceTask.objects.all():
        # Should not raise -- proves the seed data is genuinely valid per
        # MaintenanceTask.clean(), not just inserted via a bypass.
        task.full_clean()


@pytest.mark.django_db
def test_help_text_warns_about_destructive_behaviour():
    from django.core.management import get_commands, load_command_class

    assert "seed_data" in get_commands()
    command = load_command_class("maintenance", "seed_data")

    assert "delete" in command.help.lower()
