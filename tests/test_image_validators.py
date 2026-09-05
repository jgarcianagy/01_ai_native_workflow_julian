import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from maintenance.forms import StatusUpdateForm, TaskCreateForm
from maintenance.models import MaintenanceTask
from maintenance.validators import MAX_IMAGE_UPLOAD_BYTES

SIZE_ERROR = "Image must be under 10MB"
FORMAT_ERROR = "Image must be JPEG or PNG"

VALID_CREATE_DATA = {
    "title": "Fix leaky faucet",
    "description": "Faucet in room 204 bathroom is dripping constantly.",
    "location": "Room 204",
    "priority": MaintenanceTask.Priority.NORMAL,
}


def make_image_file(name, image_format, content_type):
    """Build a real, minimal in-memory image in the given Pillow format."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format=image_format)
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)


def make_png(name="issue.png"):
    return make_image_file(name, "PNG", "image/png")


def make_jpeg(name="issue.jpg"):
    return make_image_file(name, "JPEG", "image/jpeg")


def make_bmp(name="issue.bmp"):
    return make_image_file(name, "BMP", "image/bmp")


def make_non_image_file(name="not_a_photo.txt"):
    return SimpleUploadedFile(name, b"just some plain text", content_type="text/plain")


def make_oversized_jpeg(name="big.jpg", over_by=1024):
    """A valid, decodable JPEG whose total file size is just over 10MB.

    JPEG decoders (including Pillow's) stop reading at the End-Of-Image
    marker, so appending arbitrary padding bytes after a valid, tiny JPEG
    inflates the file size without breaking decodability -- confirmed this
    still passes both Image.open()+.load() and the stricter .verify() that
    Django's ImageField uses.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format="JPEG")
    data = buffer.getvalue()
    padded = data + b"\x00" * (MAX_IMAGE_UPLOAD_BYTES - len(data) + over_by)
    assert len(padded) > MAX_IMAGE_UPLOAD_BYTES
    return SimpleUploadedFile(name, padded, content_type="image/jpeg")


def make_under_limit_jpeg(name="just_under.jpg", under_by=1024):
    """A valid, decodable JPEG just under the 10MB size cap."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format="JPEG")
    data = buffer.getvalue()
    padded = data + b"\x00" * (MAX_IMAGE_UPLOAD_BYTES - len(data) - under_by)
    assert len(padded) < MAX_IMAGE_UPLOAD_BYTES
    return SimpleUploadedFile(name, padded, content_type="image/jpeg")


# -- TaskCreateForm.issue_photo (required field) -----------------------------


@pytest.mark.django_db
def test_create_form_rejects_oversized_issue_photo():
    data = {**VALID_CREATE_DATA}
    files = {"issue_photo": make_oversized_jpeg()}

    form = TaskCreateForm(data=data, files=files)

    assert not form.is_valid()
    assert SIZE_ERROR in form.errors["issue_photo"]


@pytest.mark.django_db
def test_create_form_accepts_issue_photo_just_under_size_limit():
    data = {**VALID_CREATE_DATA}
    files = {"issue_photo": make_under_limit_jpeg()}

    form = TaskCreateForm(data=data, files=files)

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_create_form_rejects_disallowed_format_issue_photo():
    data = {**VALID_CREATE_DATA}
    files = {"issue_photo": make_bmp()}

    form = TaskCreateForm(data=data, files=files)

    assert not form.is_valid()
    assert FORMAT_ERROR in form.errors["issue_photo"]


@pytest.mark.django_db
def test_create_form_accepts_jpeg_issue_photo():
    data = {**VALID_CREATE_DATA}
    files = {"issue_photo": make_jpeg()}

    form = TaskCreateForm(data=data, files=files)

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_create_form_accepts_png_issue_photo():
    data = {**VALID_CREATE_DATA}
    files = {"issue_photo": make_png()}

    form = TaskCreateForm(data=data, files=files)

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_create_form_rejects_non_image_issue_photo_via_existing_decodability_check():
    data = {**VALID_CREATE_DATA}
    files = {"issue_photo": make_non_image_file()}

    form = TaskCreateForm(data=data, files=files)

    assert not form.is_valid()
    # This is Django's pre-existing ImageField decodability check (#5), not
    # our new size/format errors -- confirms our validator doesn't crash
    # trying to read .format off an unreadable file, and doesn't shadow the
    # original error.
    errors = form.errors["issue_photo"]
    assert SIZE_ERROR not in errors
    assert FORMAT_ERROR not in errors
    assert any("valid image" in error for error in errors)


# -- StatusUpdateForm.completion_photo (optional field) ----------------------


def make_status_instance():
    return MaintenanceTask(
        title="Fix leaky faucet",
        description="Faucet in room 204 bathroom is dripping constantly.",
        location="Room 204",
        priority=MaintenanceTask.Priority.NORMAL,
        status=MaintenanceTask.Status.IN_PROGRESS,
        issue_photo=make_png("existing_issue.png"),
    )


@pytest.mark.django_db
def test_status_form_rejects_oversized_completion_photo():
    task = make_status_instance()
    task.save()
    form = StatusUpdateForm(
        data={"status": MaintenanceTask.Status.IN_PROGRESS},
        files={"completion_photo": make_oversized_jpeg()},
        instance=task,
    )

    assert not form.is_valid()
    assert SIZE_ERROR in form.errors["completion_photo"]


@pytest.mark.django_db
def test_status_form_rejects_disallowed_format_completion_photo():
    task = make_status_instance()
    task.save()
    form = StatusUpdateForm(
        data={"status": MaintenanceTask.Status.IN_PROGRESS},
        files={"completion_photo": make_bmp()},
        instance=task,
    )

    assert not form.is_valid()
    assert FORMAT_ERROR in form.errors["completion_photo"]


@pytest.mark.django_db
def test_status_form_accepts_jpeg_completion_photo():
    task = make_status_instance()
    task.save()
    form = StatusUpdateForm(
        data={"status": MaintenanceTask.Status.DONE},
        files={"completion_photo": make_jpeg()},
        instance=task,
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_status_form_accepts_png_completion_photo():
    task = make_status_instance()
    task.save()
    form = StatusUpdateForm(
        data={"status": MaintenanceTask.Status.DONE},
        files={"completion_photo": make_png("completion.png")},
        instance=task,
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_status_form_rejects_non_image_completion_photo_via_existing_decodability_check():
    task = make_status_instance()
    task.save()
    form = StatusUpdateForm(
        data={"status": MaintenanceTask.Status.IN_PROGRESS},
        files={"completion_photo": make_non_image_file()},
        instance=task,
    )

    assert not form.is_valid()
    errors = form.errors["completion_photo"]
    assert SIZE_ERROR not in errors
    assert FORMAT_ERROR not in errors
    assert any("valid image" in error for error in errors)


@pytest.mark.django_db
def test_status_form_with_no_completion_photo_is_still_valid():
    task = make_status_instance()
    task.save()
    form = StatusUpdateForm(
        data={"status": MaintenanceTask.Status.IN_PROGRESS},
        files={},
        instance=task,
    )

    assert form.is_valid(), form.errors
