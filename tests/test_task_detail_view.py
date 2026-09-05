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
    # No completion photo was attached, so no preview image renders for it
    # (the status form's file input/label are unrelated and still present).
    assert "Completion photo:</p>" not in content
    assert "alt=\"Completion photo" not in content


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
        reverse("task_detail", args=[task.pk]),
        {"technician": technician.pk, "assign_technician": "1"},
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

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"technician": "", "assign_technician": "1"},
    )
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

    client.post(
        reverse("task_detail", args=[task.pk]),
        {"technician": sam.pk, "assign_technician": "1"},
    )

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

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"technician": "", "assign_technician": "1"},
    )
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
def test_detail_page_has_status_and_completion_photo_controls(client):
    task = make_task()

    response = client.get(reverse("task_detail", args=[task.pk]))
    content = response.content.decode()

    assert 'name="status"' in content
    assert 'name="completion_photo"' in content
    assert 'name="update_status"' in content
    assert 'name="assign_technician"' in content


@pytest.mark.django_db
def test_post_status_to_in_progress_succeeds_without_photo(client):
    task = make_task(status=MaintenanceTask.Status.OPEN)

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"status": MaintenanceTask.Status.IN_PROGRESS, "update_status": "1"},
    )
    assert response.status_code in (200, 302)

    task.refresh_from_db()
    assert task.status == MaintenanceTask.Status.IN_PROGRESS


@pytest.mark.django_db
def test_post_status_done_without_photo_and_none_existing_fails_validation(client):
    task = make_task(status=MaintenanceTask.Status.OPEN)

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"status": MaintenanceTask.Status.DONE, "update_status": "1"},
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "completion photo" in content.lower()

    task.refresh_from_db()
    assert task.status == MaintenanceTask.Status.OPEN


@pytest.mark.django_db
def test_post_status_done_with_new_photo_succeeds(client):
    task = make_task(status=MaintenanceTask.Status.OPEN)

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {
            "status": MaintenanceTask.Status.DONE,
            "completion_photo": make_test_image("completion.png"),
            "update_status": "1",
        },
    )
    assert response.status_code in (200, 302)

    task.refresh_from_db()
    assert task.status == MaintenanceTask.Status.DONE
    assert task.completion_photo

    reload_response = client.get(reverse("task_detail", args=[task.pk]))
    reload_content = reload_response.content.decode()
    assert task.completion_photo.url in reload_content


@pytest.mark.django_db
def test_post_status_done_with_existing_photo_and_no_reupload_succeeds(client):
    task = make_task(
        status=MaintenanceTask.Status.IN_PROGRESS,
        completion_photo=make_test_image("existing_completion.png"),
    )
    existing_name = task.completion_photo.name

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"status": MaintenanceTask.Status.DONE, "update_status": "1"},
    )
    assert response.status_code in (200, 302)

    task.refresh_from_db()
    assert task.status == MaintenanceTask.Status.DONE
    assert task.completion_photo.name == existing_name


@pytest.mark.django_db
def test_post_status_done_with_clear_checkbox_and_no_new_photo_fails_validation(client):
    task = make_task(
        status=MaintenanceTask.Status.IN_PROGRESS,
        completion_photo=make_test_image("existing_completion.png"),
    )
    existing_name = task.completion_photo.name

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {
            "status": MaintenanceTask.Status.DONE,
            "completion_photo-clear": "on",
            "update_status": "1",
        },
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "completion photo" in content.lower()

    task.refresh_from_db()
    assert task.status == MaintenanceTask.Status.IN_PROGRESS
    assert task.completion_photo.name == existing_name


@pytest.mark.django_db
def test_post_status_away_from_done_succeeds_regardless_of_photo(client):
    task = make_task(
        status=MaintenanceTask.Status.DONE,
        completion_photo=make_test_image("existing_completion.png"),
    )

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"status": MaintenanceTask.Status.OPEN, "update_status": "1"},
    )
    assert response.status_code in (200, 302)

    task.refresh_from_db()
    assert task.status == MaintenanceTask.Status.OPEN
    # Moving away from Done does not remove an existing completion photo.
    assert task.completion_photo


@pytest.mark.django_db
def test_post_assign_technician_does_not_run_status_form_validation(client):
    technician = Technician.objects.create(name="Mike")
    task = make_task(status=MaintenanceTask.Status.OPEN)

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"technician": technician.pk, "assign_technician": "1"},
    )
    assert response.status_code in (200, 302)

    task.refresh_from_db()
    assert task.technician == technician
    # Status form's Done-requires-photo rule must not have been invoked.
    assert task.status == MaintenanceTask.Status.OPEN
