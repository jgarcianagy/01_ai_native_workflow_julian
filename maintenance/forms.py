from django import forms

from maintenance.models import MaintenanceTask


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ["title", "description", "location", "priority", "issue_photo"]
