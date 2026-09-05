"""Shared image upload validation for task photo fields.

Used by both TaskCreateForm.issue_photo and StatusUpdateForm.completion_photo
so the size cap and format allow-list are defined exactly once.
"""

from django.core.exceptions import ValidationError
from PIL import Image

MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}


def validate_task_photo(image_field_file):
    """Enforce a max file size and an image-format allow-list.

    Must run *after* Django's own `forms.ImageField` decodability check
    (which happens in the field's `to_python`, before any `clean_<field>`
    override or extra validator runs) -- by the time this is called, the
    upload is already confirmed to be a real, openable image. Format is
    determined via Pillow's `Image.format` attribute after opening the
    file, never via file extension or content-type header, since both are
    trivially spoofable.
    """
    if image_field_file.size > MAX_IMAGE_UPLOAD_BYTES:
        raise ValidationError("Image must be under 10MB")

    image_field_file.seek(0)
    try:
        image_format = Image.open(image_field_file).format
    finally:
        image_field_file.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Image must be JPEG or PNG")
