import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from maintenance.models import MaintenanceTask


def make_test_image(name="issue.png"):
    """Build a real, minimal in-memory PNG so ImageField validation passes."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def make_non_image_file(name="not_a_photo.txt"):
    return SimpleUploadedFile(name, b"just some plain text", content_type="text/plain")


VALID_DATA = {
    "title": "Fix leaky faucet",
    "description": "Faucet in room 204 bathroom is dripping constantly.",
    "location": "Room 204",
    "priority": MaintenanceTask.Priority.NORMAL,
}


@pytest.mark.django_db
def test_get_renders_form(client):
    response = client.get(reverse("task_create"))

    assert response.status_code == 200
    content = response.content.decode()
    assert '<form enctype="multipart/form-data" method="post">' in content
    assert 'name="title"' in content
    assert 'name="description"' in content
    assert 'name="location"' in content
    assert 'name="priority"' in content
    assert 'name="issue_photo"' in content
    # These fields must never appear on the creation form.
    assert 'name="status"' not in content
    assert 'name="technician"' not in content
    assert 'name="completion_photo"' not in content


@pytest.mark.django_db
def test_valid_post_creates_task_and_reshows_blank_form(client):
    data = {**VALID_DATA, "issue_photo": make_test_image()}

    response = client.post(reverse("task_create"), data, format="multipart")

    assert response.status_code == 200
    assert MaintenanceTask.objects.count() == 1

    task = MaintenanceTask.objects.get()
    assert task.title == VALID_DATA["title"]
    assert task.description == VALID_DATA["description"]
    assert task.location == VALID_DATA["location"]
    assert task.priority == VALID_DATA["priority"]
    assert task.status == MaintenanceTask.Status.OPEN
    assert task.technician is None
    assert not task.completion_photo

    content = response.content.decode()
    assert "Task created." in content
    # The re-rendered form should be blank, not still holding the submitted title.
    assert "Fix leaky faucet" not in content


@pytest.mark.django_db
def test_post_missing_title_does_not_create_task_and_preserves_other_values(client):
    data = {
        "title": "",
        "description": VALID_DATA["description"],
        "location": VALID_DATA["location"],
        "priority": VALID_DATA["priority"],
        "issue_photo": make_test_image(),
    }

    response = client.post(reverse("task_create"), data, format="multipart")

    assert response.status_code == 200
    assert MaintenanceTask.objects.count() == 0

    content = response.content.decode()
    assert "This field is required" in content
    assert VALID_DATA["description"] in content
    assert VALID_DATA["location"] in content


@pytest.mark.django_db
def test_post_non_image_issue_photo_is_rejected(client):
    data = {**VALID_DATA, "issue_photo": make_non_image_file()}

    response = client.post(reverse("task_create"), data, format="multipart")

    assert response.status_code == 200
    assert MaintenanceTask.objects.count() == 0

    content = response.content.decode()
    assert VALID_DATA["title"] in content
