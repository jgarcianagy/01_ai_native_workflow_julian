from django.http import HttpResponse
from django.shortcuts import render

from maintenance.forms import TaskCreateForm


def home(request):
    return HttpResponse("Hotel Maintenance Tracker")


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
