from django.conf import settings
from django.db import models
from django.utils import timezone


class Unit(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=120)

    class Meta:
        db_table = "units"
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"

    def __str__(self):
        return f"{self.code} — {self.title}"


class Sensor(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="sensors",
    )
    name = models.CharField(max_length=120, blank=True, null=True)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        db_column="unit_id",
        blank=True,
        null=True,
        related_name="sensors",
    )
    min_val = models.FloatField(blank=True, null=True)
    max_val = models.FloatField(blank=True, null=True)
    sampling_s = models.IntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sensors"
        verbose_name = "Датчик"
        verbose_name_plural = "Датчики"
        indexes = [
            models.Index(fields=["user"], name="sensors_user_idx"),
        ]

    def __str__(self):
        return self.name or f"Sensor {self.pk}"


class Reading(models.Model):
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        db_column="sensor_id",
        related_name="readings",
    )

    ts = models.DateTimeField(db_index=False)
    value = models.FloatField()

    class Meta:
        db_table = "readings"
        verbose_name = "Показание"
        verbose_name_plural = "Показания"

        constraints = [
            models.UniqueConstraint(fields=["sensor", "ts"], name="unique_reading_per_sensor_ts")
        ]

        indexes = [
            models.Index(fields=["ts"], name="readings_ts_idx"),
            models.Index(fields=["sensor", "ts"], name="readings_sensor_ts_idx"),
        ]
        ordering = ["-ts"]

    def __str__(self):
        return f"{self.sensor} @ {self.ts.isoformat()}: {self.value}"
