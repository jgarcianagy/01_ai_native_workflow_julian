"""Covers issue #15: shared base template + stylesheet for the dashboard,
task-creation form, and task detail page.

These tests check that the styling infrastructure is wired up (shared base
template, stylesheet link, badges carrying both a CSS class and their literal
text, a size cap on photo elements) - not the exact visual rendering.
"""

import io
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from maintenance.models import MaintenanceTask

STYLE_CSS_PATH = (
    Path(__file__).resolve().parent.parent
    / "maintenance"
    / "static"
    / "maintenance"
    / "style.css"
)


def make_test_image(name="issue.png", size=(1, 1)):
    """Build a real, in-memory PNG so ImageField validation passes."""
    buffer = io.BytesIO()
    Image.new("RGB", size, color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def make_task(**overrides):
    defaults = {
        "title": "Fix leaky faucet",
        "description": "Faucet in room 204 bathroom is dripping constantly.",
        "location": "Room 204",
        "status": MaintenanceTask.Status.OPEN,
        "priority": MaintenanceTask.Priority.URGENT,
        "issue_photo": make_test_image(),
    }
    defaults.update(overrides)
    return MaintenanceTask.objects.create(**defaults)


def test_stylesheet_exists_and_defines_no_framework_or_cdn():
    assert STYLE_CSS_PATH.exists(), "expected maintenance/static/maintenance/style.css"
    css = STYLE_CSS_PATH.read_text()
    assert css.strip(), "style.css should not be empty"
    assert "cdn." not in css
    assert "unpkg" not in css


@pytest.mark.django_db
def test_home_links_stylesheet_and_shares_base_markup(client):
    response = client.get(reverse("home"))
    content = response.content.decode()

    assert 'href="/static/maintenance/style.css"' in content
    assert "<header>" in content


@pytest.mark.django_db
def test_task_create_and_detail_share_base_markup_with_home(client):
    task = make_task()

    create_content = client.get(reverse("task_create")).content.decode()
    detail_content = client.get(reverse("task_detail", args=[task.pk])).content.decode()

    for content in (create_content, detail_content):
        assert 'href="/static/maintenance/style.css"' in content
        assert "<header>" in content


@pytest.mark.django_db
def test_home_status_badges_carry_class_and_text_per_status(client):
    open_task = MaintenanceTask.objects.create(
        title="Open task",
        description="d",
        location="Room 1",
        status=MaintenanceTask.Status.OPEN,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image("a.png"),
    )
    in_progress_task = MaintenanceTask.objects.create(
        title="In progress task",
        description="d",
        location="Room 2",
        status=MaintenanceTask.Status.IN_PROGRESS,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image("b.png"),
    )
    done_task = MaintenanceTask.objects.create(
        title="Done task",
        description="d",
        location="Room 3",
        status=MaintenanceTask.Status.DONE,
        priority=MaintenanceTask.Priority.NORMAL,
        issue_photo=make_test_image("c.png"),
        completion_photo=make_test_image("c2.png"),
    )

    content = client.get(reverse("home")).content.decode()

    for task, css_class in (
        (open_task, "status-open"),
        (in_progress_task, "status-in_progress"),
        (done_task, "status-done"),
    ):
        assert css_class in content
        assert task.get_status_display() in content


@pytest.mark.django_db
def test_priority_badge_is_separate_element_from_status_badge(client):
    task = make_task(
        status=MaintenanceTask.Status.OPEN, priority=MaintenanceTask.Priority.URGENT
    )

    content = client.get(reverse("task_detail", args=[task.pk])).content.decode()

    assert 'class="badge badge-status status-open"' in content
    assert 'class="badge badge-priority priority-urgent"' in content
    assert task.get_priority_display() in content


@pytest.mark.django_db
def test_photo_elements_have_a_size_capping_rule_in_stylesheet(client):
    task = make_task(issue_photo=make_test_image("big.png", size=(50, 50)))

    content = client.get(reverse("task_detail", args=[task.pk])).content.decode()

    assert 'class="task-photo"' in content

    css = STYLE_CSS_PATH.read_text()
    assert ".task-photo" in css
    assert "max-width" in css
    assert "max-height" in css


@pytest.mark.django_db
def test_validation_errors_have_a_dedicated_stylesheet_rule(client):
    task = make_task(status=MaintenanceTask.Status.OPEN)

    response = client.post(
        reverse("task_detail", args=[task.pk]),
        {"status": MaintenanceTask.Status.DONE, "update_status": "1"},
    )
    content = response.content.decode()

    assert "errorlist" in content

    css = STYLE_CSS_PATH.read_text()
    assert ".errorlist" in css


@pytest.mark.django_db
def test_empty_state_has_a_dedicated_stylesheet_rule(client):
    assert MaintenanceTask.objects.count() == 0

    content = client.get(reverse("home")).content.decode()

    assert 'class="empty-state"' in content

    css = STYLE_CSS_PATH.read_text()
    assert ".empty-state" in css
