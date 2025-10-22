from django.contrib import admin
from .models import Unit, Facility, Sensor, Actuator, Rule, RuleSensor, Alert, Command, CommandArg

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)

class CommandArgInline(admin.TabularInline):
    model = CommandArg
    extra = 0

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ("name", "facility", "user", "unit", "sampling_s", "created_at")
    list_filter = ("facility", "user", "unit")
    search_fields = ("name",)

@admin.register(Actuator)
class ActuatorAdmin(admin.ModelAdmin):
    list_display = ("name", "sensor", "type", "range_min", "range_max", "step")
    list_filter = ("type", "sensor__facility")
    search_fields = ("name",)

class RuleSensorInline(admin.TabularInline):
    model = RuleSensor
    extra = 0

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "severity", "enabled", "window_s", "created_at")
    list_filter = ("enabled", "severity", "user")
    inlines = [RuleSensorInline]
    search_fields = ("name", "expr")

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("state", "rule", "sensor", "started_at", "ended_at", "ack_by", "ack_at")
    list_filter = ("state", "rule__severity")
    search_fields = ("message",)

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ("actuator", "command", "status", "issued_by", "issued_at", "completed_at")
    list_filter = ("status", "command", "actuator__type")
    inlines = [CommandArgInline]
