from django.http import HttpResponse


def home(request):
    return HttpResponse("Hotel Maintenance Tracker")
