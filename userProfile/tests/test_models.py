from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from userProfile.models import UserProfile  

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.today = timezone.now().date()

    def _valid_birth_date(self):
        return self.today - timedelta(days=365 * 20)

    def test_email_is_lowercased_on_clean(self):
        user = UserProfile(
            username="User1",
            email="USER@TEST.COM",
            date_of_birth=self._valid_birth_date(),
            role="student",
            password="password",
        )

        user.full_clean() 
        self.assertEqual(user.email, "user@test.com")

    def test_date_of_birth_must_be_in_the_past(self):
        user = UserProfile(
            username="User2",
            email="user2@test.com",
            date_of_birth=self.today,  
            role="student",
            password="password",
        )

        with self.assertRaises(ValidationError) as ctx:
            user.full_clean()

        self.assertIn("detail", ctx.exception.error_dict)
        messages = [e.message for e in ctx.exception.error_dict["detail"]]
        self.assertIn("Date of birth must be in the past.", messages)

    def test_date_of_birth_not_unrealistically_old(self):
        unrealistic_threshold = self.today.replace(year=self.today.year - 121)
        very_old = unrealistic_threshold - timedelta(days=1)

        user = UserProfile(
            username="User3",
            email="user3@test.com",
            date_of_birth=very_old,
            role="student",
            password="password",
        )

        with self.assertRaises(ValidationError) as ctx:
            user.full_clean()

        self.assertIn("Date of birth is not realistic.", str(ctx.exception))

    def test_date_of_birth_not_too_young(self):
        young_threshold = self.today.replace(year=self.today.year - 1)
        too_young = young_threshold + timedelta(days=1)

        user = UserProfile(
            username="User4",
            email="user4@test.com",
            date_of_birth=too_young,
            role="student",
            password="password",
        )

        with self.assertRaises(ValidationError) as ctx:
            user.full_clean()

        self.assertIn("User must be at least 14 years old.", str(ctx.exception))

    def test_str_returns_username(self):
        user = UserProfile.objects.create(
            username="UserStr",
            email="userstr@test.com",
            date_of_birth=self._valid_birth_date(),
            role="student",
            password="password",
        )

        self.assertEqual(str(user), "UserStr")