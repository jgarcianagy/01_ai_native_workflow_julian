from django.shortcuts import render

from maintenance.forms import TaskCreateForm
from maintenance.models import MaintenanceTask


def home(request):
    tasks = MaintenanceTask.objects.select_related("technician").order_by(
        "-created_at"
    )
    return render(request, "maintenance/home.html", {"tasks": tasks})


def task_create(request):
    created = False
    if request.method == "POST":
        form = TaskCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            created = True
            form = TaskCreateForm()
    else:
        form = TaskCreateForm()

    return render(
        request,
        "maintenance/task_create.html",
        {"form": form, "created": created},
    )
