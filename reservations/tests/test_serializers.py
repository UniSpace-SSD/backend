from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from rest_framework.exceptions import ValidationError
from reservations.serializers import ReservationSerializer
from reservations.models import Reservation, ReservationStatus
from spaces.models import Space, Building

User = get_user_model()


class ReservationSerializerTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="Via 123 Test")
        self.space = Space.objects.create(name="Test Space", building=self.building, capacity=10)
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            date_of_birth=timezone.now(),
            password="password",
        )

        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

        self.future_start = timezone.now() + timedelta(days=1)
        self.future_end = self.future_start + timedelta(hours=1)

    def test_valid_serializer(self):
        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Test Reservation",
        }
        serializer = ReservationSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_overlap(self):
        # User already has a reservation
        Reservation.objects.create(
            space=self.space,
            created_by=self.user,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED,
        )

        other_space = Space.objects.create(
            name="Other Space", building=self.building, capacity=5
        )

        data = {
            "space": other_space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Overlap User",
        }
        serializer = ReservationSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn(
            "You already have a reservation in this timeslot.",
            str(serializer.errors["non_field_errors"]),
        )

    def test_partial_update_uses_instance_dates_and_excludes_itself(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.user,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        data = {
            "header": "Updated header",
        }
        serializer = ReservationSerializer(
            instance=reservation,
            data=data,
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated = serializer.save()
        self.assertEqual(updated.header, "Updated header")
        self.assertEqual(updated.start_at, self.future_start)
        self.assertEqual(updated.end_at, self.future_end)

    def test_partial_update_with_new_end_uses_existing_start(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.user,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        new_end = self.future_end + timedelta(hours=1)

        data = {
            "end_at": new_end,
        }
        serializer = ReservationSerializer(
            instance=reservation,
            data=data,
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.start_at, self.future_start)
        self.assertEqual(updated.end_at, new_end)

    def test_validate_skips_overlap_when_missing_dates(self):
        data = {
            "space": self.space.id,
            "header": "No dates yet",
            # no start_at / end_at
        }

        serializer = ReservationSerializer(
            data=data,
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)