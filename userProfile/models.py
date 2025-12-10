from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class UserProfile(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Studente'),
        ('professor', 'Professore'),
    )

    email = models.EmailField(unique=True, verbose_name="Email", error_messages={"unique": "Email already used"})
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Data di nascita")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Ruolo")

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'date_of_birth', 'role']

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = self.email.lower()

        if self.date_of_birth is None:
            return

        today = timezone.now().date()

        if self.date_of_birth >= today:
            raise ValidationError({'detail': "Date of birth must be in the past."})

        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

        if age > 120:
            raise ValidationError({'detail': "Date of birth is not realistic."})

        if age < 14:
            raise ValidationError({'detail': "User must be at least 14 years old."})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
