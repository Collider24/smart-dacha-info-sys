from django.contrib import admin
from .models import Sensor, Reading


class ReadingInline(admin.TabularInline):
    model = Reading
    extra = 0
    fields = ("value", "measured_at")
    ordering = ("-measured_at",)


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display  = ("identifier", "name", "owner", "metric", "unit", "created_at")
    list_filter   = ("metric", "owner")
    search_fields = ("identifier", "name")
    inlines       = [ReadingInline]


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display  = ("sensor", "value", "measured_at", "created_at")
    list_filter   = ("sensor__metric",)
    search_fields = ("sensor__identifier", "sensor__name")
    autocomplete_fields = ("sensor",)
    date_hierarchy = "measured_at"
