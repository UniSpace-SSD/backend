from django.db import models
from django.contrib.auth.models import AbstractUser

class UserProfile(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Studente'),
        ('professor', 'Professore'),
    )

    email = models.EmailField(unique=True, verbose_name="Email", error_messages={"unique": "Email already used"})
    date_of_birth = models.DateField(verbose_name="Data di nascita")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Ruolo")

    def __str__(self):
        return self.username