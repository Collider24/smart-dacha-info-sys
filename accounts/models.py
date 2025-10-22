from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    OPERATOR = "operator", "Operator"
    VIEWER = "viewer", "Viewer"

class User(AbstractUser):
    role = models.CharField(
        max_length=16,
        choices=UserRole.choices,
        default=UserRole.VIEWER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
