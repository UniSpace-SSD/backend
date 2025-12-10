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
        # Un solo "now" per tutti i test, così evitiamo effetti strani di fuso/ora legale
        self.now = timezone.now().replace(minute=0, second=0, microsecond=0)

        # Giorno futuro "base" per le prenotazioni
        self.base_day = (self.now + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        self.future_start = self.base_day
        self.future_end = self.future_start + timedelta(hours=1)

        # Spazi / building
        self.building = Building.objects.create(
            name="Test Building",
            address="Via 123 Test",
        )
        self.space = Space.objects.create(
            name="Test Space",
            building=self.building,
            capacity=10,
        )

        # Utente studente (default role = 'student')
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=18),
            password="password",
        )

        # Utente admin/staff
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=30),
            password="password",
            is_staff=True,
        )

        # Utente professore
        self.professor = User.objects.create_user(
            username="professor",
            email="prof@test.com",
            date_of_birth=timezone.localdate() - relativedelta(years=35),
            password="password",
            role="professor",
        )

        self.factory = RequestFactory()

    # ---------- Helper per creare request con user ----------
    def _get_request_for(self, user):
        req = self.factory.get("/")
        req.user = user
        return req

    # ---------- Test base di validità ----------
    def test_student_valid_same_day_reservation(self):
        """Lo studente può creare una reservation nello stesso giorno."""
        request = self._get_request_for(self.student)
        data = {
            "space": self.space.id,
            "start_at": self.future_start,
            "end_at": self.future_end,
            "header": "Test Reservation",
        }
        serializer = ReservationSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # ---------- Regola: studente solo stesso giorno ----------
    def test_student_cannot_cross_midnight(self):
        """Lo studente NON può creare prenotazioni che superano la mezzanotte (giorni diversi)."""
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

    # ---------- Regola: admin non può creare reservations ----------
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

    # ---------- Professore: può anche attraversare i giorni ----------
    def test_professor_can_cross_days(self):
        """Il professore NON ha il vincolo 'stesso giorno'."""
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

    # ---------- Overlapping per utente ----------
    def test_user_overlap(self):
        """Se lo stesso utente ha già una reservation confermata nello slot, viene bloccato."""

        # Reservation esistente (studente)
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

    # ---------- Partial update: usa le date esistenti se non passate ----------
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

    # ---------- Nessuna data -> niente controllo di overlap ----------
    def test_validate_skips_overlap_when_missing_dates(self):
        request = self._get_request_for(self.student)

        data = {
            "space": self.space.id,
            "header": "No dates yet",
            # start_at / end_at mancanti
        }

        serializer = ReservationSerializer(
            data=data,
            partial=True,
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
