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
        self.building = Building.objects.create(name="Test Building", address="123 Test St")
        self.space = Space.objects.create(name="Test Room", building=self.building, capacity=10)
        self.user = User.objects.create_user(username="testuser", email="test@test.com", date_of_birth=timezone.now(), password="password")

        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.future_start = timezone.now() + timedelta(days=1)
        self.future_end = self.future_start + timedelta(hours=1)

    def test_valid_serializer(self):
        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Test Reservation"
        }
        serializer = ReservationSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_overlap(self):
        # User already has a reservation
        Reservation.objects.create(
            space=self.space,
            created_by=self.user,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED
        )

        # Try to book another space (or same space) at same time
        other_space = Space.objects.create(name="Other Room", building=self.building, capacity=5)

        data = {
            "space": other_space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Overlap User"
        }
        serializer = ReservationSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn("You already have a reservation in this timeslot.", str(serializer.errors["non_field_errors"]))
