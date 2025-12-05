from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from reservations.models import Reservation, ReservationStatus
from spaces.models import Space, Building

User = get_user_model()


class ReservationViewSetTest(APITestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="123 Test St")
        self.space = Space.objects.create(name="Test Room", building=self.building, capacity=10)

        self.student = User.objects.create_user(username="student", email="student@test.com", password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", password="password",
                                              is_staff=True)

        self.future_start = timezone.now() + timedelta(days=1)
        self.future_end = self.future_start + timedelta(hours=1)

        # URL for list/create is usually inferred from router, assuming standard router usage
        # I'll assume /api/reservations/ or similar.
        # Since I don't know the exact URL conf, I will use reverse if I can guess the name,
        # or just assume standard router names 'reservation-list', 'reservation-detail'
        self.list_url = reverse('reservation-list')

    def test_create_reservation(self):
        self.client.force_authenticate(user=self.student)
        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "API Reservation"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Reservation.objects.get().created_by, self.student)

    def test_list_reservations(self):
        # Create a reservation for student
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end
        )

        # Student sees their reservation
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Pagination might wrap this in 'results'
        # If paginated, response.data['results']
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

        # Another user sees nothing
        other_user = User.objects.create_user(username="other", email="other@test.com", password="password")
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.list_url)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 0)
        else:
            self.assertEqual(len(response.data), 0)

        # Admin sees all (if logic allows, views.py said "if user.is_staff: return qs")
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_cancel_action(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )
        url = reverse('reservation-cancel', args=[reservation.id])

        self.client.force_authenticate(user=self.student)
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_confirm_action(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )
        url = reverse('reservation-confirm', args=[reservation.id])

        # Student cannot confirm
        self.client.force_authenticate(user=self.student)
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Admin can confirm
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)
