from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from reservations.models import Reservation, ReservationStatus
from reservations.serializers import ReservationSerializer
from spaces.models import Space, Building


User = get_user_model()


class ReservationSerializerTest(TestCase):
    def setUp(self):
        self.now = timezone.now().replace(minute=0, second=0, microsecond=0)

        self.base_day = (self.now + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        self.future_start = self.base_day
        self.future_end = self.future_start + timedelta(hours=1)

        self.building = Building.objects.create(
            name="Test Building",
            address="Via 123 Test",
        )
        self.space = Space.objects.create(
            name="Test Space",
            building=self.building,
            capacity=10,
        )

        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=18),
            password="password",
        )

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=30),
            password="password",
            is_staff=True,
        )

        self.professor = User.objects.create_user(
            username="professor",
            email="prof@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=35),
            password="password",
            role="professor",
        )

        self.factory = RequestFactory()

    def _get_request_for(self, user):
        req = self.factory.get("/")
        req.user = user
        return req

    def test_student_valid_same_day_reservation(self):
        request = self._get_request_for(self.student)
        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Test Reservation",
        }
        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_student_cannot_cross_midnight(self):
        request = self._get_request_for(self.student)

        start = self.base_day.replace(hour=22)
        end = (self.base_day + timedelta(days=1)).replace(hour=1)

        data = {
            "space": self.space.id,
            "start_at": start,
            "end_at": end,
            "header": "Cross-day Reservation",
        }

        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)
        self.assertIn(
            "Students can only create reservations within the same day.",
            str(serializer.errors["detail"]),
        )

    def test_admin_cannot_create_reservation(self):
        request = self._get_request_for(self.admin)

        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Admin Reservation",
        }

        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)
        self.assertIn(
            "Admins are not allowed to create reservations.",
            str(serializer.errors["detail"]),
        )

    def test_professor_can_cross_days(self):
        request = self._get_request_for(self.professor)

        start = self.base_day.replace(hour=22)
        end = (self.base_day + timedelta(days=1)).replace(hour=1)

        data = {
            "space": self.space.id,
            "start_at": start,
            "end_at": end,
            "header": "Prof Cross-day Reservation",
        }

        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_overlap(self):

        Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.CONFIRMED,
        )

        other_space = Space.objects.create(
            name="Other Space",
            building=self.building,
            capacity=5,
        )

        request = self._get_request_for(self.student)

        data = {
            "space": other_space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Overlap User",
        }
        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)
        self.assertIn(
            "You already have a reservation in this timeslot.",
            str(serializer.errors["detail"]),
        )

    def test_partial_update_uses_instance_dates_and_excludes_itself(self):
        request = self._get_request_for(self.student)

        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
            start_at=self.future_start,
            end_at=self.future_end,
            status=ReservationStatus.PENDING,
        )

        data = {
            "header": "Updated header",
            # nessun start_at / end_at -> devono rimanere invariati
        }
        serializer = ReservationSerializer(
            instance=reservation,
            data=data,
            partial=True,
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.header, "Updated header")
        self.assertEqual(updated.start_at, self.future_start)
        self.assertEqual(updated.end_at, self.future_end)

    def test_partial_update_with_new_end_uses_existing_start(self):
        request = self._get_request_for(self.student)

        reservation = Reservation.objects.create(
            space=self.space,
            created_by=self.student,
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
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.start_at, self.future_start)
        self.assertEqual(updated.end_at, new_end)

    def test_validate_skips_overlap_when_missing_dates(self):
        request = self._get_request_for(self.student)

        data = {
            "space": self.space.id,
            "header": "No dates yet",
        }

        serializer = ReservationSerializer(
            data=data,
            partial=True,
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_professor_cannot_create_reservation_wrong_department(self):
        professor_other_dept = User.objects.create_user(
            username="prof_other",
            email="prof_other@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=35),
            password="password",
            role="professor",
        )
        professor_other_dept.department = "DIMES"
        professor_other_dept.save()

        request = self._get_request_for(professor_other_dept)

        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Wrong Department",
        }

        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)
        self.assertIn(
            "Can't visualize reservations for a space that not belongs to your department.",
            str(serializer.errors["detail"]),
        )

    def test_create_method(self):
        request = self._get_request_for(self.student)
        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Create Test",
        }
        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())
        reservation = serializer.save(created_by=self.student)
        self.assertIsNotNone(reservation.pk)
        self.assertEqual(reservation.created_by, self.student)