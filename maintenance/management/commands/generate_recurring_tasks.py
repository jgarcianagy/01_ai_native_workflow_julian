import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from maintenance.models import MaintenanceTask, RecurrenceRule


class Command(BaseCommand):
    help = (
        "Creates a new MaintenanceTask for every RecurrenceRule whose interval "
        "has come due, and updates that rule's last_generated_date to today."
    )

    def handle(self, *args, **options):
        today = timezone.localdate()

        created_count = 0
        for rule in RecurrenceRule.objects.all():
            is_due = rule.last_generated_date is None or (
                rule.last_generated_date + datetime.timedelta(days=rule.interval_days)
                <= today
            )
            if not is_due:
                continue

            MaintenanceTask.objects.create(
                title=rule.title,
                description=rule.description,
                location=rule.location,
                priority=rule.priority,
            )
            rule.last_generated_date = today
            rule.save(update_fields=["last_generated_date"])
            created_count += 1

        self.stdout.write(f"Created {created_count} task(s).")
