import io

import pytest
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
def test_home_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_home_lists_task_fields(client):
    technician = Technician.objects.create(name="Mike")
    task = MaintenanceTask.objects.create(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.URGENT,
        technician=technician,
        issue_photo=make_test_image(),
    )

    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert task.title in content
    assert task.get_status_display() in content
    assert task.get_priority_display() in content
    assert task.location in content
    assert technician.name in content


@pytest.mark.django_db
def test_home_shows_tasks_of_every_status(client):
    open_task = MaintenanceTask.objects.create(
        title="Open task",
        description="An open task.",
        location="Room 101",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image("open.png"),
    )
    in_progress_task = MaintenanceTask.objects.create(
        title="In progress task",
        description="A task being worked on.",
        location="Room 102",
        status=MaintenanceTask.Status.IN_PROGRESS,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image("in_progress.png"),
    )
    done_task = MaintenanceTask.objects.create(
        title="Done task",
        description="A finished task.",
        location="Room 103",
        status=MaintenanceTask.Status.DONE,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image("done.png"),
        completion_photo=make_test_image("done_completion.png"),
    )

    response = client.get("/")
    content = response.content.decode()

    assert response.status_code == 200
    assert open_task.title in content
    assert in_progress_task.title in content
    assert done_task.title in content


@pytest.mark.django_db
def test_home_shows_unassigned_for_task_without_technician(client):
    task = MaintenanceTask.objects.create(
        title="Replace hallway light",
        description="Flickering light in 3rd floor hallway.",
        location="3rd Floor Hallway",
        priority=MaintenanceTask.Priority.LOW,
        issue_photo=make_test_image(),
    )
    assert task.technician is None

    response = client.get("/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Unassigned" in content


@pytest.mark.django_db
def test_home_empty_state_shows_message_when_no_tasks(client):
    assert MaintenanceTask.objects.count() == 0

    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "No tasks" in content
