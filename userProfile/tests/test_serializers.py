from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from django.contrib.sessions.middleware import SessionMiddleware  # <--- NEW

from userProfile.models import UserProfile
from userProfile.serializers import CustomRegisterSerializer


class CustomRegisterSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.valid_data = {
            "username": "testuser",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
            "email": "user@example.com",
            "first_name": "Mario",
            "last_name": "Rossi",
            "date_of_birth": (timezone.now().date() - timedelta(days=365 * 20)),
            "role": "student",
            "department": "DEMACS",
        }

        request = self.factory.post("/auth/register/", self.valid_data)
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()

        self.request = request

    def test_get_cleaned_data_contains_custom_fields(self):
        serializer = CustomRegisterSerializer(
            data=self.valid_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        cleaned = serializer.get_cleaned_data()
        self.assertEqual(cleaned["first_name"], self.valid_data["first_name"])
        self.assertEqual(cleaned["last_name"], self.valid_data["last_name"])
        self.assertEqual(cleaned["date_of_birth"], self.valid_data["date_of_birth"])
        self.assertEqual(cleaned["role"], self.valid_data["role"])
        self.assertEqual(cleaned["email"], self.valid_data["email"])
        self.assertEqual(cleaned["department"], self.valid_data["department"])

    def test_save_sets_custom_fields_on_user(self):
        serializer = CustomRegisterSerializer(
            data=self.valid_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save(self.request)

        self.assertIsInstance(user, UserProfile)
        self.assertEqual(user.username, self.valid_data["username"])
        self.assertEqual(user.first_name, self.valid_data["first_name"])
        self.assertEqual(user.last_name, self.valid_data["last_name"])
        self.assertEqual(user.date_of_birth, self.valid_data["date_of_birth"])
        self.assertEqual(user.role, self.valid_data["role"])
        self.assertEqual(user.email, self.valid_data["email"])
        self.assertTrue(user.check_password(self.valid_data["password1"]))
