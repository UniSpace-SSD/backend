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
        self.building = Building.objects.create(name="Test Building", address="Via 123 Test")
        self.space = Space.objects.create(name="Test Space", building=self.building, capacity=10)

        self.student = User.objects.create_user(username="student", email="student@test.com", date_of_birth=timezone.now(), password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", date_of_birth=timezone.now(), password="password",
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
            end_at=self.future_start,  
            header="Invalid Date"
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_overlapping_reservation(self):
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start, 
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED
        )

        # New reservations with overlapping times
        reservation = Reservation(
            space=self.space,
            created_by=self.admin,
            start_at=self.future_start, 
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED  
        )

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

        self.assertTrue(reservation.can_be_cancelled_by(self.student))

        self.assertTrue(reservation.can_be_cancelled_by(self.admin))

        other_user = User.objects.create_user(username="other", email="other@test.com", date_of_birth=timezone.now(), password="password")
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

        self.assertFalse(reservation.can_be_cancelled_by(self.student))

    def test_confirm_method(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )

        with self.assertRaises(ValidationError):
            reservation.confirm(self.student)

        reservation.confirm(self.admin)
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)

    def test_cannot_create_reservation_in_the_past(self):
        past_start = timezone.now() - timedelta(hours=1)
        future_end = timezone.now() + timedelta(hours=1)

        reservation = Reservation(
            space=self.space,
            created_by=self.student,
            start_at=past_start, # Invalid start time
            end_at=future_end,  # Invalid end time
            header="Past start reservation",
        )

        with self.assertRaises(ValidationError) as ctx:
            reservation.full_clean()

        self.assertIn(
            "You cannot create reservations in the past.",
            str(ctx.exception),
        )

    def test_cannot_confirm_non_pending_reservation(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CANCELLED  # Invalid: not pending
        )

        with self.assertRaises(ValidationError) as ctx:
            reservation.confirm(self.admin)

        self.assertIn(
            "Only pending reservations can be confirmed.",
            str(ctx.exception),
        )