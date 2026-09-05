from django import forms

from maintenance.models import MaintenanceTask
from maintenance.validators import validate_task_photo


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ["title", "description", "location", "priority", "issue_photo"]

    def clean_issue_photo(self):
        photo = self.cleaned_data.get("issue_photo")
        if photo:
            validate_task_photo(photo)
        return photo


class TechnicianAssignForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ["technician"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["technician"].required = False
        self.fields["technician"].empty_label = "Unassigned"


class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = ["status", "completion_photo"]

    def clean_completion_photo(self):
        photo = self.cleaned_data.get("completion_photo")
        if photo:
            validate_task_photo(photo)
        return photo
