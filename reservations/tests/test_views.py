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

        url = reverse('reservations:reservation-me')

        # Student: should work
        self.client.force_authenticate(user=self.student)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

        # Admin: should be forbidden (403)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_get_queryset_swagger_fake_view(self):
        view = ReservationViewSet()
        view.swagger_fake_view = True
        view.request = None
        self.assertEqual(view.get_queryset().count(), 0)

    def test_me_admin_forbidden(self):
        """Admin non può accedere all'endpoint /me."""
        url = reverse("reservations:reservation-me")
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_by_space_student_only_own(self):
        """Student vede solo le proprie reservation per uno spazio."""
        own = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        other = Reservation.objects.create(
            space=self.space,
            created_by=self.admin,
            start_at=self.future_start + timedelta(hours=2),
            end_at=self.future_end + timedelta(hours=2),
        )

        url = reverse("reservations:reservation-by-space", args=[self.space.id])
        self.client.force_authenticate(user=self.student)

        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(own.id))

    def test_by_space_professor_wrong_department(self):
        professor = User.objects.create_user(
            username="prof4",
            email="prof4@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=35),
            password="password",
        )
        professor.role = "professor"
        professor.department = "DIMES"
        professor.save()

        url = reverse("reservations:reservation-by-space", args=[self.space.id])
        self.client.force_authenticate(user=professor)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_by_space_professor_correct_department(self):
        """Professor del dipartimento giusto vede tutte le reservation dello spazio."""
        professor = User.objects.create_user(
            username="prof5",
            email="prof5@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=35),
            password="password",
        )
        professor.role = "professor"
        professor.department = self.building.department
        professor.save()

        res1 = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        res2 = Reservation.objects.create(
            space=self.space,
            created_by=self.admin,
            start_at=self.future_start + timedelta(hours=2),
            end_at=self.future_end + timedelta(hours=2),
        )

        url = reverse("reservations:reservation-by-space", args=[self.space.id])
        self.client.force_authenticate(user=professor)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_by_space_admin_sees_all(self):
        """Admin vede tutte le reservation dello spazio."""
        res1 = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        res2 = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start + timedelta(hours=2),
            end_at=self.future_end + timedelta(hours=2),
        )

        url = reverse("reservations:reservation-by-space", args=[self.space.id])
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_queryset_unauthenticated(self):
        """Unauthenticated user gets empty queryset."""
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        view = ReservationViewSet()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_get_queryset_professor(self):
        """Professor vede tutte le reservation del proprio dipartimento."""
        professor = User.objects.create_user(
            username="prof6",
            email="prof6@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=35),
            password="password",
        )
        professor.role = "professor"
        professor.department = self.building.department
        professor.save()

        # Reservation nel dipartimento del professor
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        # Altro building/dipartimento
        other_building = Building.objects.create(
            name="Other Building",
            address="Via Other",
            department="OTHER_DEPT"
        )
        other_space = Space.objects.create(
            name="Other Space",
            building=other_building,
            capacity=5
        )
        Reservation.objects.create(
            space=other_space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = professor

        view = ReservationViewSet()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().space, self.space)

    def test_permission_allows_professor_same_department(self):
        """Professor può accedere alle reservation del proprio dipartimento."""
        professor = User.objects.create_user(
            username="prof7",
            email="prof7@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=35),
            password="password",
        )
        professor.role = "professor"
        professor.department = self.building.department
        professor.save()

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
        request.user = professor

        self.assertTrue(permission.has_object_permission(request, None, reservation))

    def test_permission_denies_professor_different_department(self):
        """Professor non può accedere alle reservation di altri dipartimenti."""
        professor = User.objects.create_user(
            username="prof8",
            email="prof8@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=35),
            password="password",
        )
        professor.role = "professor"
        professor.department = "DIMES"
        professor.save()

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
        request.user = professor

        self.assertFalse(permission.has_object_permission(request, None, reservation))

    def test_get_queryset_not_swagger_not_authenticated(self):
        """Test get_queryset quando swagger_fake_view=False e user non autenticato."""
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        view = ReservationViewSet()
        view.swagger_fake_view = False
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_by_space_superuser_sees_all(self):
        """Superuser vede tutte le reservation (testa il branch admin/superuser in by_space)."""
        superuser = User.objects.create_user(
            username="superuser",
            email="super@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=30),
            password="password",
            is_superuser=True
        )

        res1 = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        res2 = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start + timedelta(hours=2),
            end_at=self.future_end + timedelta(hours=2),
        )

        url = reverse("reservations:reservation-by-space", args=[self.space.id])
        self.client.force_authenticate(user=superuser)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_queryset_student_sees_only_own(self):
        """Student nel get_queryset vede solo le proprie reservation."""
        student2 = User.objects.create_user(
            username="student2",
            email="student2@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=20),
            password="password"
        )

        # Reservation dello student principale
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        # Reservation di altro student
        Reservation.objects.create(
            space=self.space,
            created_by=student2,
            start_at=self.future_start + timedelta(hours=2),
            end_at=self.future_end + timedelta(hours=2),
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.student

        view = ReservationViewSet()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().created_by, self.student)

    def test_get_queryset_admin_sees_all(self):
        """Admin nel get_queryset vede tutte le reservation."""
        # Reservation di student
        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
        )

        # Altra reservation
        other_student = User.objects.create_user(
            username="other_student",
            email="other@test.com",
            date_of_birth=timezone.now().date() - relativedelta(years=19),
            password="password"
        )
        Reservation.objects.create(
            space=self.space,
            created_by=other_student,
            start_at=self.future_start + timedelta(hours=2),
            end_at=self.future_end + timedelta(hours=2),
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.admin

        view = ReservationViewSet()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(qs.count(), 2)

    def test_confirm_saves_and_refreshes(self):
        """Test che confirm salvi correttamente dopo aver impostato lo status."""
        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING
        )
        
        url = reverse('reservations:reservation-confirm', args=[reservation.id])
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica che sia stato salvato nel DB
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)
        
        # Verifica che la response contenga i dati aggiornati
        self.assertEqual(response.data['status'], ReservationStatus.CONFIRMED)