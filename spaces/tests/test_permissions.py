from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from spaces.permissions import IsAdminOrReadOnly
from rest_framework.permissions import SAFE_METHODS
from django.utils import timezone

from dateutil.relativedelta import relativedelta


User = get_user_model()

class IsAdminOrReadOnlyTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdminOrReadOnly()
        self.student = User.objects.create_user(username="student", email="student@test.com", date_of_birth=timezone.now().date() - relativedelta(years=18), password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", date_of_birth=timezone.now().date() - relativedelta(years=18), password="password",
                                              is_staff=True)

    def test_read_only_access(self):
        for method in SAFE_METHODS:
            request = self.factory.generic(method, '/')
            request.user = self.student
            self.assertTrue(self.permission.has_permission(request, None))

            request.user = None  # Unauthenticated user
            self.assertTrue(self.permission.has_permission(request, None))

    def test_write_access_student(self):
        for method in ["POST", "PUT", "DELETE"]:
            request = self.factory.generic(method, '/')
            request.user = self.student
            self.assertFalse(self.permission.has_permission(request, None))

    def test_write_access_admin(self):
        for method in ["POST", "PUT", "DELETE"]:
            request = self.factory.generic(method, '/')
            request.user = self.admin
            self.assertTrue(self.permission.has_permission(request, None))
