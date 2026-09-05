from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Technician(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class MaintenanceTask(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DONE = "DONE", "Done"

    class Priority(models.TextChoices):
        URGENT = "URGENT", "Urgent"
        NORMAL = "NORMAL", "Normal"
        LOW = "LOW", "Low"

    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    issue_photo = models.ImageField(upload_to="task_photos/issue/")
    completion_photo = models.ImageField(
        upload_to="task_photos/completion/", blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    priority = models.CharField(max_length=20, choices=Priority.choices)
    technician = models.ForeignKey(
        "Technician", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.status == self.Status.DONE and not self.completion_photo:
            raise ValidationError(
                {
                    "completion_photo": (
                        "A completion photo is required before a task can be "
                        "marked Done."
                    )
                }
            )


class RecurrenceRule(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    priority = models.CharField(
        max_length=20, choices=MaintenanceTask.Priority.choices
    )
    interval_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    last_generated_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
