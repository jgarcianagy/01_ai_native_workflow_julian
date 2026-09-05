import datetime

import pytest
from django.core.exceptions import ValidationError

from maintenance.models import MaintenanceTask, RecurrenceRule


@pytest.mark.django_db
def test_create_rule_with_all_required_fields_and_no_last_generated_date():
    rule = RecurrenceRule.objects.create(
        title="Replace HVAC filters",
        description="Replace air filters in all guest room HVAC units.",
        location="All Guest Rooms",
        priority=MaintenanceTask.Priority.NORMAL,
        interval_days=90,
    )

    assert rule.pk is not None
    assert rule.last_generated_date is None


@pytest.mark.django_db
def test_create_rule_with_last_generated_date_set():
    generated_date = datetime.date(2026, 1, 1)
    rule = RecurrenceRule.objects.create(
        title="Test smoke detectors",
        description="Test smoke detectors on every floor.",
        location="All Floors",
        priority=MaintenanceTask.Priority.URGENT,
        interval_days=30,
        last_generated_date=generated_date,
    )

    assert rule.last_generated_date == generated_date


@pytest.mark.django_db
def test_str_returns_title():
    rule = RecurrenceRule.objects.create(
        title="Check fire extinguishers",
        description="Inspect fire extinguishers in stairwells.",
        location="Stairwells",
        priority=MaintenanceTask.Priority.LOW,
        interval_days=7,
    )

    assert str(rule) == "Check fire extinguishers"


@pytest.mark.django_db
def test_full_clean_rejects_invalid_priority():
    rule = RecurrenceRule(
        title="Check fire extinguishers",
        description="Inspect fire extinguishers in stairwells.",
        location="Stairwells",
        priority="bogus",
        interval_days=7,
    )

    with pytest.raises(ValidationError):
        rule.full_clean()


@pytest.mark.django_db
def test_full_clean_rejects_interval_days_zero():
    rule = RecurrenceRule(
        title="Check fire extinguishers",
        description="Inspect fire extinguishers in stairwells.",
        location="Stairwells",
        priority=MaintenanceTask.Priority.LOW,
        interval_days=0,
    )

    with pytest.raises(ValidationError):
        rule.full_clean()


@pytest.mark.django_db
def test_non_standard_interval_days_saves_successfully():
    rule = RecurrenceRule.objects.create(
        title="Deep clean carpets",
        description="Deep clean carpets in common areas.",
        location="Common Areas",
        priority=MaintenanceTask.Priority.NORMAL,
        interval_days=14,
    )

    rule.full_clean()
    assert rule.interval_days == 14
