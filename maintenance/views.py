from django.shortcuts import get_object_or_404, redirect, render

from maintenance.forms import TaskCreateForm, TechnicianAssignForm
from maintenance.models import MaintenanceTask


def home(request):
    tasks = MaintenanceTask.objects.select_related("technician").order_by(
        "-created_at"
    )
    return render(request, "maintenance/home.html", {"tasks": tasks})


def task_detail(request, pk):
    task = get_object_or_404(MaintenanceTask, pk=pk)

    if request.method == "POST":
        form = TechnicianAssignForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("task_detail", pk=task.pk)
    else:
        form = TechnicianAssignForm(instance=task)

    return render(
        request,
        "maintenance/task_detail.html",
        {"task": task, "form": form},
    )


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
