import datetime
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image

from maintenance.models import MaintenanceTask, RecurrenceRule, Technician


def make_seed_image(name, color):
    """Build a real, minimal in-memory PNG so ImageField validation passes.

    Same pattern as make_test_image() in tests/test_maintenance_task.py,
    adapted so it can be used outside a test file (unique filename per call
    so uploads don't collide on disk).
    """
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color=color).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


class Command(BaseCommand):
    help = (
        "DESTRUCTIVE: deletes ALL existing Technician, MaintenanceTask, and "
        "RecurrenceRule rows, then recreates a fixed set of local dev seed "
        "data (technicians, tasks across every status/priority/assignment "
        "combination, and a recurrence rule) so the dashboard has something "
        "to show. For local development only — never run against a "
        "production database."
    )

    def handle(self, *args, **options):
        # Clear first. MaintenanceTask.technician uses on_delete=SET_NULL, so
        # deleting Technicians does NOT cascade-delete tasks -- each queryset
        # must be cleared explicitly.
        MaintenanceTask.objects.all().delete()
        RecurrenceRule.objects.all().delete()
        Technician.objects.all().delete()

        technicians = [
            Technician.objects.create(name=name)
            for name in ["Mike Alvarez", "Priya Nair", "Jordan Lee", "Sam Okafor"]
        ]
        mike, priya, jordan, sam = technicians

        today = timezone.localdate()

        def make_task(
            title,
            description,
            location,
            status,
            priority,
            technician=None,
            with_completion_photo=False,
        ):
            task = MaintenanceTask(
                title=title,
                description=description,
                location=location,
                status=status,
                priority=priority,
                technician=technician,
                issue_photo=make_seed_image(
                    f"issue-{MaintenanceTask.objects.count()}-{title[:20]}.png",
                    "red",
                ),
            )
            if with_completion_photo:
                task.completion_photo = make_seed_image(
                    f"completion-{title[:20]}.png", "green"
                )
            # Validate before saving so seeded data models only states the
            # app itself considers valid (e.g. Done requires a completion
            # photo) instead of bypassing clean() via a raw .create().
            task.full_clean()
            task.save()
            return task

        # Covers all three statuses, all three priorities, a mix of
        # assigned/unassigned tasks, and both completion-photo states.
        make_task(
            title="Fix leaky faucet",
            description="Faucet in room 204 bathroom is dripping constantly.",
            location="Room 204",
            status=MaintenanceTask.Status.OPEN,
            priority=MaintenanceTask.Priority.URGENT,
            technician=None,
        )
        make_task(
            title="Replace hallway light",
            description="Flickering light in 3rd floor hallway.",
            location="3rd Floor Hallway",
            status=MaintenanceTask.Status.OPEN,
            priority=MaintenanceTask.Priority.LOW,
            technician=mike,
        )
        make_task(
            title="Repair AC unit",
            description="AC unit in room 101 is not cooling.",
            location="Room 101",
            status=MaintenanceTask.Status.IN_PROGRESS,
            priority=MaintenanceTask.Priority.URGENT,
            technician=priya,
        )
        make_task(
            title="Unclog kitchen drain",
            description="Kitchen sink in the staff break room drains slowly.",
            location="Staff Break Room",
            status=MaintenanceTask.Status.IN_PROGRESS,
            priority=MaintenanceTask.Priority.NORMAL,
            technician=None,
        )
        make_task(
            title="Fix elevator button panel",
            description="Floor 5 button in the main elevator is unresponsive.",
            location="Main Elevator",
            status=MaintenanceTask.Status.DONE,
            priority=MaintenanceTask.Priority.URGENT,
            technician=jordan,
            with_completion_photo=True,
        )
        make_task(
            title="Repaint lobby scuff marks",
            description="Scuff marks on the lobby wall near the entrance.",
            location="Lobby",
            status=MaintenanceTask.Status.DONE,
            priority=MaintenanceTask.Priority.LOW,
            technician=sam,
            with_completion_photo=True,
        )
        make_task(
            title="Replace pool area umbrella",
            description="One of the poolside umbrellas is torn and needs replacing.",
            location="Pool Area",
            status=MaintenanceTask.Status.DONE,
            priority=MaintenanceTask.Priority.NORMAL,
            technician=mike,
            with_completion_photo=True,
        )
        make_task(
            title="Adjust thermostat in conference room",
            description="Thermostat in the main conference room reads incorrectly.",
            location="Conference Room",
            status=MaintenanceTask.Status.OPEN,
            priority=MaintenanceTask.Priority.NORMAL,
            technician=None,
        )

        # RecurrenceRule overdue enough that generate_recurring_tasks
        # visibly creates a task when run afterward.
        RecurrenceRule.objects.create(
            title="Replace HVAC filters",
            description="Replace air filters in all guest room HVAC units.",
            location="All Guest Rooms",
            priority=MaintenanceTask.Priority.NORMAL,
            interval_days=90,
            last_generated_date=today - datetime.timedelta(days=200),
        )
        RecurrenceRule.objects.create(
            title="Test smoke detectors",
            description="Test smoke detectors on every floor.",
            location="All Floors",
            priority=MaintenanceTask.Priority.URGENT,
            interval_days=30,
            last_generated_date=None,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Technician.objects.count()} technician(s), "
                f"{MaintenanceTask.objects.count()} task(s), and "
                f"{RecurrenceRule.objects.count()} recurrence rule(s)."
            )
        )
