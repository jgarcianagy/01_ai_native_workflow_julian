from django.shortcuts import get_object_or_404, redirect, render

from maintenance.forms import StatusUpdateForm, TaskCreateForm, TechnicianAssignForm
from maintenance.models import MaintenanceTask


def home(request):
    tasks = MaintenanceTask.objects.select_related("technician").order_by(
        "-created_at"
    )
    return render(request, "maintenance/home.html", {"tasks": tasks})


def task_detail(request, pk):
    task = get_object_or_404(MaintenanceTask, pk=pk)

    if request.method == "POST":
        if "assign_technician" in request.POST:
            assign_form = TechnicianAssignForm(request.POST, instance=task)
            status_form = StatusUpdateForm(instance=task)
            if assign_form.is_valid():
                assign_form.save()
                return redirect("task_detail", pk=task.pk)
        elif "update_status" in request.POST:
            status_form = StatusUpdateForm(request.POST, request.FILES, instance=task)
            assign_form = TechnicianAssignForm(instance=task)
            if status_form.is_valid():
                status_form.save()
                return redirect("task_detail", pk=task.pk)
        else:
            assign_form = TechnicianAssignForm(instance=task)
            status_form = StatusUpdateForm(instance=task)
    else:
        assign_form = TechnicianAssignForm(instance=task)
        status_form = StatusUpdateForm(instance=task)

    return render(
        request,
        "maintenance/task_detail.html",
        {"task": task, "assign_form": assign_form, "status_form": status_form},
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
