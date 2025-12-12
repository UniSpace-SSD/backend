from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid

from spaces.models import Space


class ReservationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending approval"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"


class Reservation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_reservations",
    )

    header = models.CharField(
        max_length=255,
        help_text="Motivo della prenotazione (es. Lezione Analisi 1)",
        blank=True
    )

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    status = models.CharField(
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True) 

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["space", "start_at", "end_at"]),
            models.Index(fields=["cancelled_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.header}: {self.space} {self.start_at} - {self.end_at}"

    def clean(self):
        super().clean()

        if self.start_at >= self.end_at:
            raise ValidationError(
                {"detail": "End time must be after start time."}
            )

        if self.start_at < timezone.now():
            raise ValidationError(
                {"detail": "You cannot create reservations in the past."}
            )

        # controllo overlapping sulla stessa resource
        overlapping_space_qs = Reservation.objects.filter(
            space=self.space,
            status=ReservationStatus.CONFIRMED, 
        ).exclude(
            pk=self.pk
        ).filter(
            models.Q(
                start_at__gte=self.start_at,
                start_at__lte=self.end_at,
            ) |
            models.Q(
                end_at__gte=self.start_at,
                end_at__lte=self.end_at,
            )
        )

        if overlapping_space_qs.exists():
            raise ValidationError(
                {"detail": "Resource is already reserved in this timeslot."}
            )

    def can_be_cancelled_by(self, user) -> bool:
        if self.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            return False

        if not user or not user.is_authenticated:
            return False

        # Admin
        if user.is_staff or user.is_superuser:
            return True

        # Owner
        if user == self.created_by:
            return True

        # Professor del dipartimento dello spazio
        if getattr(user, "role", None) == "professor":
            return getattr(user, "department", None) == self.space.building.department

        return False

    def cancel(self, user):
        if not self.can_be_cancelled_by(user):
            raise ValidationError({"detail": "User is not allowed to cancel this reservation."})

        self.status = ReservationStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at", "updated_at"])

    def confirm(self, approver):
        if self.status != ReservationStatus.PENDING:
            raise ValidationError("Only pending reservations can be confirmed.")

        # Admin sempre ok
        if approver.is_staff or approver.is_superuser:
            self.status = ReservationStatus.CONFIRMED
            return

        # Professor ok solo nel suo dipartimento
        if getattr(approver, "role", None) == "professor":
            if approver.department != self.space.building.department:
                raise ValidationError("Professor cannot confirm reservations outside their department.")
            self.status = ReservationStatus.CONFIRMED
            return

        raise ValidationError("Only admins or professors can confirm reservations.")