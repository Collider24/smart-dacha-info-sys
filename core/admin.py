from django.contrib import admin
from .models import (Unit, Facility, Sensor, Actuator, Rule, RuleSensor, Alert, Command, SensorActuator,
                     RuleCommand)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)

class SensorActuatorInlineForSensor(admin.TabularInline):
    model = SensorActuator
    fk_name = "sensor"
    extra = 0
    autocomplete_fields = ("actuator",)

class SensorActuatorInlineForActuator(admin.TabularInline):
    model = SensorActuator
    fk_name = "actuator"
    extra = 0
    autocomplete_fields = ("sensor",)

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ("name", "facility", "user", "unit", "sampling_s", "created_at")
    list_filter = ("facility", "user", "unit")
    search_fields = ("name", "facility__name")
    inlines = [SensorActuatorInlineForSensor]

@admin.register(Actuator)
class ActuatorAdmin(admin.ModelAdmin):
    list_display = ("name", "facility", "type", "range_min", "range_max", "step", "sensors_list")
    list_filter = ("type", "facility")
    search_fields = ("name", "facility__name", "sensors__name")
    inlines = [SensorActuatorInlineForActuator]
    autocomplete_fields = ("facility",)

    def sensors_list(self, obj):
        names = list(obj.sensors.values_list("name", flat=True)[:5])
        more = obj.sensors.count() - len(names)
        return ", ".join(names) + (f" (+{more})" if more > 0 else "")
    sensors_list.short_description = "Датчики"


class RuleSensorInline(admin.TabularInline):
    model = RuleSensor
    extra = 0

class RuleCommandInline(admin.TabularInline):
    model = RuleCommand
    extra = 0

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "severity", "enabled", "window_s", "created_at")
    list_filter = ("enabled", "severity", "user")
    inlines = [RuleSensorInline, RuleCommandInline]
    search_fields = ("name", "expr")

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("state", "rule", "started_at", "ended_at", "ack_by", "ack_at")
    list_filter = ("state", "rule__severity")
    search_fields = ("message",)

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ("actuator", "name", "created_by", "created_at", "commands_args", "status")
    list_filter = ("status", "name", "actuator__type")