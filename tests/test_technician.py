import pytest

from maintenance.models import Technician


@pytest.mark.django_db
def test_technician_str_returns_name():
    technician = Technician.objects.create(name="Mike")
    assert str(technician) == "Mike"
