import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from maintenance.models import MaintenanceTask, Technician


def make_test_image(name="issue.png"):
    """Build a real, minimal in-memory PNG so ImageField validation passes."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@pytest.mark.django_db
def test_create_task_with_all_required_fields_and_no_technician():
    task = MaintenanceTask.objects.create(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image(),
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
        issue_photo=make_test_image(),
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
        issue_photo=make_test_image(),
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
        issue_photo=make_test_image(),
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
        issue_photo=make_test_image(),
    )

    with pytest.raises(ValidationError):
        task.full_clean()


@pytest.mark.django_db
def test_full_clean_rejects_missing_issue_photo():
    task = MaintenanceTask(
        title="Fix window",
        description="Window latch is broken in room 305.",
        location="Room 305",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.NORMAL,
    )

    with pytest.raises(ValidationError):
        task.full_clean()


@pytest.mark.django_db
def test_task_can_be_created_without_completion_photo():
    task = MaintenanceTask.objects.create(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image(),
    )

    assert task.pk is not None
    assert not task.completion_photo


@pytest.mark.django_db
def test_full_clean_rejects_done_task_without_completion_photo():
    task = MaintenanceTask(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.DONE,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image(),
    )

    with pytest.raises(ValidationError) as exc_info:
        task.full_clean()

    assert "completion_photo" in exc_info.value.message_dict
    assert "completion photo" in str(exc_info.value.message_dict["completion_photo"])


@pytest.mark.django_db
def test_full_clean_accepts_done_task_with_completion_photo():
    task = MaintenanceTask(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.DONE,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image(),
        completion_photo=make_test_image("completion.png"),
    )

    task.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [MaintenanceTask.Status.OPEN, MaintenanceTask.Status.IN_PROGRESS],
)
def test_full_clean_accepts_non_done_task_without_completion_photo(status):
    task = MaintenanceTask(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=status,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image(),
    )

    task.full_clean()


@pytest.mark.django_db
def test_full_clean_still_enforces_rule_after_unrelated_field_edit():
    task = MaintenanceTask.objects.create(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.DONE,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image(),
        completion_photo=make_test_image("completion.png"),
    )

    task.title = "Fix leaky faucet (updated)"
    task.full_clean()

    task.completion_photo = None
    with pytest.raises(ValidationError) as exc_info:
        task.full_clean()

    assert "completion_photo" in exc_info.value.message_dict
