from django.conf import settings
from django.db import models
from django.utils import timezone


class Sensor(models.Model):
    class Metric(models.TextChoices):
        TEMPERATURE = "temperature", "Температура"
        HUMIDITY    = "humidity",    "Влажность"
        SOIL        = "soil",        "Влажность почвы"
        CO2         = "co2",         "CO₂"
        PRESSURE    = "pressure",    "Давление"
        LIGHT       = "light",       "Освещённость"
        OTHER       = "other",       "Другое"

    owner        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sensors",
        verbose_name="Владелец",
    )
    identifier   = models.CharField("Идентификатор", max_length=64)
    name         = models.CharField("Название", max_length=128, blank=True)
    metric       = models.CharField("Измеряемая величина",
                                    max_length=32, choices=Metric.choices)
    unit         = models.CharField("Единица измерения", max_length=16, blank=True)
    created_at   = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Датчик"
        verbose_name_plural = "Датчики"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "identifier"],
                name="unique_sensor_per_owner"
            )
        ]
        indexes = [
            models.Index(fields=["owner", "metric"]),
        ]

    def __str__(self):
        return self.name or f"{self.identifier} ({self.get_metric_display()})"


class Reading(models.Model):
    sensor      = models.ForeignKey(Sensor, on_delete=models.CASCADE,
                                    related_name="readings", verbose_name="Датчик")
    value       = models.FloatField("Значение")
    measured_at = models.DateTimeField("Время измерения", default=timezone.now)
    created_at  = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        verbose_name = "Показание"
        verbose_name_plural = "Показания"
        ordering = ["-measured_at"]
        indexes = [
            models.Index(fields=["sensor", "measured_at"]),
        ]

    def __str__(self):
        return f"{self.sensor} = {self.value} {self.sensor.unit} @ {self.measured_at:%Y-%m-%d %H:%M}"
