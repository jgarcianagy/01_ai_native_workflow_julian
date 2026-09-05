from django.contrib import admin

from .models import RecurrenceRule, Technician

admin.site.register(Technician)
admin.site.register(RecurrenceRule)
