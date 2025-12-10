from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from reservations.models import Reservation, ReservationStatus
from reservations.views import ReservationViewSet
from spaces.models import Space, Building
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser
from reservations.permissions import IsOwnerOrStaff

from dateutil.relativedelta import relativedelta


User = get_user_model()


class OnePerPagePagination(PageNumberPagination):
    page_size = 1
    

class ReservationViewSetTest(APITestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="Via 123 Test")
        self.space = Space.objects.create(name="Test Space", building=self.building, capacity=10)

        self.student = User.objects.create_user(username="student", email="student@test.com", date_of_birth=timezone.now().date() - relativedelta(years=18), password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", date_of_birth=timezone.now().date() - relativedelta(years=18), password="password",
                                              is_staff=True)

        self.future_start = timezone.now() + timedelta(days=1)
        self.future_end = self.future_start + timedelta(hours=1)

        self.list_url = reverse('reservations:reservation-list')

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
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  

        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

        other_user = User.objects.create_user(username="other", email="other@test.com", date_of_birth=timezone.now().date() - relativedelta(years=18), password="password")
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.list_url)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 0)
        else:
            self.assertEqual(len(response.data), 0)

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
        url = reverse('reservations:reservation-cancel', args=[reservation.id])

        self.client.force_authenticate(user=self.student)
        response = self.client.patch(url)
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
        url = reverse('reservations:reservation-confirm', args=[reservation.id])

        self.client.force_authenticate(user=self.student)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)

    def test_partial_update_not_allowed(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end
        )
        url = reverse('reservations:reservation-detail', args=[reservation.id])

        self.client.force_authenticate(user=self.student)
        data = {"header": "Updated Header"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Test cancelling an already cancelled reservation
    def test_cancel_bad_request(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CANCELLED
        )
        url = reverse('reservations:reservation-cancel', args=[reservation.id])

        self.client.force_authenticate(user=self.student)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_action_me(self):
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end
        )
        Reservation.objects.create(
            space=self.space,
            created_by=self.admin,
            start_at=self.future_start,
            end_at=self.future_end
        )

        url = reverse('reservations:reservation-me')

        self.client.force_authenticate(user=self.student)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1) 

    def test_action_me_paginated(self):
        old_pagination_class = ReservationViewSet.pagination_class
        ReservationViewSet.pagination_class = OnePerPagePagination

        try:
            Reservation.objects.create(
                space=self.space,
                created_by=self.student,
                start_at=self.future_start,
                end_at=self.future_end,
            )
            Reservation.objects.create(
                space=self.space,
                created_by=self.student,
                start_at=self.future_start + timedelta(hours=1),
                end_at=self.future_end + timedelta(hours=1),
            )

            url = reverse("reservations:reservation-me")
            self.client.force_authenticate(user=self.student)

            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertIn("results", response.data)
            self.assertEqual(response.data["count"], 2)
            self.assertEqual(len(response.data["results"]), 1) 

        finally:
            ReservationViewSet.pagination_class = old_pagination_class

    def test_str_representation(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            header="Test Reservation"
        )
        expected_str = f"Test Reservation: {self.space} {self.future_start} - {self.future_end}"
        self.assertEqual(str(reservation), expected_str)

    def test_permission_denies_unauthenticated_user(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        permission = IsOwnerOrStaff()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        self.assertFalse(permission.has_object_permission(request, None, reservation))

    def test_permission_allows_staff(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        permission = IsOwnerOrStaff()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.admin  # is_staff=True nel tuo setUp

        self.assertTrue(permission.has_object_permission(request, None, reservation))

    def test_permission_allows_owner(self):
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        permission = IsOwnerOrStaff()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.student  # owner

        self.assertTrue(permission.has_object_permission(request, None, reservation))

    def test_permission_denies_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            email="other@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=18),
            password="password",
        )

        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        permission = IsOwnerOrStaff()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = other_user

        self.assertFalse(permission.has_object_permission(request, None, reservation))