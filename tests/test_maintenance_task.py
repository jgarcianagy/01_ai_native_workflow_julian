import pytest
from django.core.exceptions import ValidationError

from maintenance.models import MaintenanceTask, Technician


@pytest.mark.django_db
def test_create_task_with_all_required_fields_and_no_technician():
    task = MaintenanceTask.objects.create(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.NORMAL,
    )

    assert task.pk is not None
    assert task.technician is None
    assert task.status == MaintenanceTask.Status.OPEN
    assert task.priority == MaintenanceTask.Priority.NORMAL
    assert task.created_at is not None
    assert task.updated_at is not None


@pytest.mark.django_db
def test_str_returns_title():
    task = MaintenanceTask.objects.create(
        title="Replace hallway light",
        description="Flickering light in 3rd floor hallway.",
        location="3rd Floor Hallway",
        priority=MaintenanceTask.Priority.LOW,
    )

    assert str(task) == "Replace hallway light"


@pytest.mark.django_db
def test_deleting_assigned_technician_sets_task_technician_to_none():
    technician = Technician.objects.create(name="Mike")
    task = MaintenanceTask.objects.create(
        title="Repair AC unit",
        description="AC unit in room 101 is not cooling.",
        location="Room 101",
        priority=MaintenanceTask.Priority.URGENT,
        technician=technician,
    )

    technician.delete()
    task.refresh_from_db()

    assert task.technician is None
    assert MaintenanceTask.objects.filter(pk=task.pk).exists()


@pytest.mark.django_db
def test_full_clean_rejects_invalid_status():
    task = MaintenanceTask(
        title="Fix window",
        description="Window latch is broken in room 305.",
        location="Room 305",
        status="bogus",
        priority=MaintenanceTask.Priority.NORMAL,
    )

    with pytest.raises(ValidationError):
        task.full_clean()


@pytest.mark.django_db
def test_full_clean_rejects_invalid_priority():
    task = MaintenanceTask(
        title="Fix window",
        description="Window latch is broken in room 305.",
        location="Room 305",
        status=MaintenanceTask.Status.OPEN,
        priority="bogus",
    )

    with pytest.raises(ValidationError):
        task.full_clean()
