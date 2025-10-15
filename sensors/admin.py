from django.contrib import admin
from .models import Unit, Sensor, Reading


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")


class ReadingInline(admin.TabularInline):
    model = Reading
    fields = ("ts", "value")
    extra = 1
    ordering = ("-ts",)


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "name",
        "unit",
        "min_val",
        "max_val",
        "sampling_s",
        "created_at",
        "updated_at",
    )
    list_filter = ("unit", "sampling_s")
    search_fields = ("name", "user__username", "user__email")
    inlines = [ReadingInline]
    raw_id_fields = ("user",)
    list_select_related = ("user", "unit")


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("sensor", "ts", "value")
    list_filter = ("sensor__unit",)
    search_fields = ("sensor__name", "sensor__id")
    autocomplete_fields = ("sensor",)
    date_hierarchy = "ts"
    ordering = ("-ts",)
    list_select_related = ("sensor",)
