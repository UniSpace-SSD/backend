from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import timedelta
from reservations.models import Reservation, ReservationStatus
from spaces.models import Space, Building

User = get_user_model()


class ReservationModelTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="123 Test St")
        self.space = Space.objects.create(name="Test Room", building=self.building, capacity=10)

        self.student = User.objects.create_user(username="student", email="student@test.com", password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", password="password",
                                              is_staff=True)

        self.future_start = timezone.now() + timedelta(days=1)
        self.future_end = self.future_start + timedelta(hours=1)

    def test_create_valid_reservation(self):
        reservation = Reservation(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            header="Study Session"
        )
        reservation.full_clean()
        reservation.save()
        self.assertIsNotNone(reservation.pk)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_create_invalid_dates(self):
        reservation = Reservation(
            space=self.space,
            created_by=self.student,
            start_at=self.future_end,
            end_at=self.future_start,  # End before start
            header="Invalid Date"
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_overlapping_reservation(self):
        # Create a confirmed reservation
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED
        )

        # Try to create another overlapping reservation
        reservation = Reservation(
            space=self.space,
            created_by=self.admin,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED  # Simulate trying to confirm it directly or check clean logic
        )

        # clean() checks for overlapping confirmed reservations
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_can_be_cancelled_by(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )

        # Owner can cancel
        self.assertTrue(reservation.can_be_cancelled_by(self.student))

        # Admin can cancel
        self.assertTrue(reservation.can_be_cancelled_by(self.admin))

        # Random user cannot cancel
        other_user = User.objects.create_user(username="other", email="other@test.com", password="password")
        self.assertFalse(reservation.can_be_cancelled_by(other_user))

    def test_cancel_method(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )

        reservation.cancel(self.student)
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

        # Cannot cancel already cancelled
        self.assertFalse(reservation.can_be_cancelled_by(self.student))

    def test_confirm_method(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )

        # Student cannot confirm
        with self.assertRaises(ValidationError):
            reservation.confirm(self.student)

        # Admin can confirm
        reservation.confirm(self.admin)
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)
