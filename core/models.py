from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

# ===== Enums =====
class FacilityType(models.TextChoices):
    HOUSE = "house"
    SAUNA = "sauna"
    GREENHOUSE = "greenhouse"
    WOODSHED = "woodshed"
    GARAGE = "garage"
    CELLAR = "cellar"
    POOL = "pool"
    GRILL = "grill"

class AlertState(models.TextChoices):
    OPEN = "open"
    ACK = "ack"
    CLOSED = "closed"

class SeverityLevel(models.TextChoices):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ActuatorType(models.TextChoices):
    BINARY = "binary"
    LEVEL = "level"
    SETPOINT = "setpoint"

class CommandStatus(models.TextChoices):
    QUEUED = "queued"
    SENT = "sent"
    SUCCESS = "success"
    FAILED = "failed"

# ===== Reference tables =====
class Unit(models.Model):
    code = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.code} ({self.title})"

class Facility(models.Model):
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=32, choices=FacilityType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["type"])]

    def __str__(self):
        return f"{self.name} [{self.type}]"

# ===== Sensors =====
class Sensor(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sensors")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="sensors")
    name = models.CharField(max_length=120)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="sensors")
    min_val = models.FloatField(null=True, blank=True)
    max_val = models.FloatField(null=True, blank=True)
    sampling_s = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["facility"]),
            models.Index(fields=["user"]),
            models.Index(fields=["unit"]),
            models.Index(fields=["name"]),
        ]
        unique_together = [("facility", "name")]

    def __str__(self):
        return f"{self.facility}:{self.name}"

# ===== Actuators =====
class Actuator(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="actuators")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=16, choices=ActuatorType.choices)
    range_min = models.FloatField(null=True, blank=True)
    range_max = models.FloatField(null=True, blank=True)
    step = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["sensor"]), models.Index(fields=["type"])]

    def __str__(self):
        return f"{self.sensor}::{self.name}"

# ===== Rules =====
class Rule(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="rules")
    name = models.CharField(max_length=160)
    expr = models.TextField(help_text="Напр.: pm2_5 > 50")
    window_s = models.IntegerField(default=0)
    severity = models.CharField(max_length=16, choices=SeverityLevel.choices, default=SeverityLevel.WARNING)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    sensors = models.ManyToManyField(Sensor, through="RuleSensor", related_name="rules")

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["enabled"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self):
        return self.name

class RuleSensor(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("rule", "sensor")]
        indexes = [models.Index(fields=["sensor"])]

    def __str__(self):
        return f"{self.rule_id}->{self.sensor_id}"

# ===== Alerts =====
class Alert(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="alerts")
    sensor = models.ForeignKey(Sensor, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=16, choices=AlertState.choices, default=AlertState.OPEN)
    message = models.TextField(null=True, blank=True)
    ack_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="acked_alerts")
    ack_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["rule"]),
            models.Index(fields=["sensor"]),
            models.Index(fields=["state"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self):
        return f"[{self.state}] {self.rule.name} @ {self.started_at}"

# ===== Commands =====
class Command(models.Model):
    actuator = models.ForeignKey(Actuator, on_delete=models.CASCADE, related_name="commands")
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="commands")
    issued_at = models.DateTimeField(auto_now_add=True)
    command = models.CharField(max_length=32, help_text="ON|OFF|SET")
    status = models.CharField(max_length=16, choices=CommandStatus.choices, default=CommandStatus.QUEUED)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["actuator"]),
            models.Index(fields=["issued_at"]),
            models.Index(fields=["status"]),
        ]

    # core/models.py (внутри Command)
    def clean(self):
        from django.core.exceptions import ValidationError
        a_type = self.actuator.type
        if self.command.upper() == "SET" and a_type not in (ActuatorType.LEVEL, ActuatorType.SETPOINT):
            raise ValidationError("SET допустим только для actuator type LEVEL/SETPOINT.")
        if self.command.upper() in ("ON", "OFF") and a_type != ActuatorType.BINARY:
            raise ValidationError("ON/OFF допустимы только для actuator type BINARY.")

    def __str__(self):
        return f"{self.actuator} <- {self.command} ({self.status})"

class CommandArg(models.Model):
    command = models.ForeignKey(Command, on_delete=models.CASCADE, related_name="args")
    name = models.CharField(max_length=64)
    value = models.TextField()

    class Meta:
        unique_together = [("command", "name")]

    def __str__(self):
        return f"{self.command_id}:{self.name}={self.value}"
