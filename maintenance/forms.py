from django import forms

from maintenance.models import MaintenanceTask


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ["title", "description", "location", "priority", "issue_photo"]


class TechnicianAssignForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ["technician"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["technician"].required = False
        self.fields["technician"].empty_label = "Unassigned"
