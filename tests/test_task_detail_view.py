import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from maintenance.models import MaintenanceTask, Technician


def make_test_image(name="issue.png"):
    """Build a real, minimal in-memory PNG so ImageField validation passes."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def make_task(**overrides):
    defaults = {
        "title": "Fix leaky faucet",
        "description": "Faucet in room 204 bathroom is dripping constantly.",
        "location": "Room 204",
        "status": MaintenanceTask.Status.OPEN,
        "priority": MaintenanceTask.Priority.NORMAL,
        "issue_photo": make_test_image(),
    }
    defaults.update(overrides)
    return MaintenanceTask.objects.create(**defaults)


@pytest.mark.django_db
def test_get_detail_shows_all_fields(client):
    technician = Technician.objects.create(name="Mike")
    task = make_task(
        completion_photo=make_test_image("completion.png"),
        technician=technician,
    )

    response = client.get(reverse("task_detail", args=[task.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert task.title in content
    assert task.description in content
    assert task.location in content
    assert task.get_status_display() in content
    assert task.get_priority_display() in content
    assert technician.name in content
    assert task.issue_photo.url in content
    assert task.completion_photo.url in content


@pytest.mark.django_db
def test_get_detail_omits_completion_photo_when_absent(client):
    task = make_task()

    response = client.get(reverse("task_detail", args=[task.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert task.issue_photo.url in content
    # No completion photo was attached, so nothing photo-related for it renders.
    assert "Completion photo" not in content


@pytest.mark.django_db
def test_get_detail_shows_unassigned_when_no_technician(client):
    task = make_task()

    response = client.get(reverse("task_detail", args=[task.pk]))

    assert response.status_code == 200
    assert "Unassigned" in response.content.decode()


@pytest.mark.django_db
def test_get_detail_with_nonexistent_pk_returns_404(client):
    response = client.get(reverse("task_detail", args=[999999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_post_assigns_technician_and_persists(client):
    technician = Technician.objects.create(name="Mike")
    task = make_task()

    response = client.post(
        reverse("task_detail", args=[task.pk]), {"technician": technician.pk}
    )
    assert response.status_code in (200, 302)

    # Reload independently of the POST response to prove it actually persisted.
    reload_response = client.get(reverse("task_detail", args=[task.pk]))
    content = reload_response.content.decode()

    task.refresh_from_db()
    assert task.technician == technician
    assert technician.name in content
    assert f'value="{technician.pk}" selected' in content


@pytest.mark.django_db
def test_post_blank_selection_clears_technician(client):
    technician = Technician.objects.create(name="Mike")
    task = make_task(technician=technician)

    response = client.post(reverse("task_detail", args=[task.pk]), {"technician": ""})
    assert response.status_code in (200, 302)

    reload_response = client.get(reverse("task_detail", args=[task.pk]))
    content = reload_response.content.decode()

    task.refresh_from_db()
    assert task.technician is None
    assert "Unassigned" in content


@pytest.mark.django_db
def test_reassigning_overwrites_previous_technician(client):
    mike = Technician.objects.create(name="Mike")
    sam = Technician.objects.create(name="Sam")
    task = make_task(technician=mike)

    client.post(reverse("task_detail", args=[task.pk]), {"technician": sam.pk})

    task.refresh_from_db()
    assert task.technician == sam


@pytest.mark.django_db
def test_detail_page_renders_with_zero_technicians(client):
    assert Technician.objects.count() == 0
    task = make_task()

    response = client.get(reverse("task_detail", args=[task.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'name="technician"' in content
    assert "Unassigned" in content


@pytest.mark.django_db
def test_post_with_zero_technicians_only_allows_unassigned(client):
    assert Technician.objects.count() == 0
    task = make_task()

    response = client.post(reverse("task_detail", args=[task.pk]), {"technician": ""})
    assert response.status_code in (200, 302)

    task.refresh_from_db()
    assert task.technician is None


@pytest.mark.django_db
def test_home_page_links_to_task_detail(client):
    task = make_task()

    response = client.get(reverse("home"))

    assert response.status_code == 200
    content = response.content.decode()
    detail_url = reverse("task_detail", args=[task.pk])
    assert f'href="{detail_url}"' in content

    detail_response = client.get(detail_url)
    assert detail_response.status_code == 200
    assert task.title in detail_response.content.decode()


@pytest.mark.django_db
def test_detail_page_has_no_status_or_completion_photo_controls(client):
    task = make_task()

    response = client.get(reverse("task_detail", args=[task.pk]))
    content = response.content.decode()

    assert 'name="status"' not in content
    assert 'name="completion_photo"' not in content
