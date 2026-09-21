from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Model User kustom Prismata.
    Menambahkan field 'role' ke user bawaan Django.
    """
    ROLE_CHOICES = [
        ("pelamar", "Pelamar"),
        ("hrd", "HRD"),
        ("admin", "Admin"),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="pelamar",
        verbose_name="Peran",
    )

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Pengguna"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
