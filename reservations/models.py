import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from spaces.models import Space


class ReservationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending approval"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"
    REJECTED = "REJECTED", "Rejected"
    EXPIRED = "EXPIRED", "Expired"


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

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["space", "start_at", "end_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.header}: {self.space} {self.start_at} - {self.end_at}"

    def clean(self):
        super().clean()

        if self.start_at >= self.end_at:
            raise ValidationError("Start time must be before end time.")

        # controllo overlapping sulla stessa resource
        overlapping_qs = Reservation.objects.filter(
        space=self.space,
        status=ReservationStatus.CONFIRMED,   # solo confermate
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

        if overlapping_qs.exists():
            raise ValidationError("Resource is already reserved in this timeslot.")


    """"
    def can_be_cancelled_by(self, user) -> bool:
        if self.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            raise ValidationError("Only pending or confirmed reservations can be cancelled.") # TODO: better exception

        try:
            role = user.profile.role
        except Profile.DoesNotExist:
            raise ValidationError("User profile does not exist.") # TODO: better exception

        if role in [UserRole.STUDENT or UserRole.TEACHER] and user == self.created_by:
            return True
        elif role in [UserRole.STAFF, UserRole.ADMIN]:
            return True

        return False

    """
    def cancel(self, user):
        #if not self.can_be_cancelled_by(user):
        #    raise ValidationError("User is not allowed to cancel this reservation.")
        self.status = ReservationStatus.CANCELLED


    def confirm(self, approver):
        if self.status != ReservationStatus.PENDING:
            raise ValidationError("Only pending reservations can be confirmed.")

        """
        try:
            role = approver.profile.role
        except Profile.DoesNotExist:
            raise ValidationError("User profile does not exist.") # TODO: better exception

        if role != UserRole.ADMIN:
            raise ValidationError("Only admins can confirm reservations.") # TODO: better exception
        """
        self.status = ReservationStatus.CONFIRMED
