from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from spaces.permissions import IsAdminOrReadOnly
from rest_framework.permissions import SAFE_METHODS

User = get_user_model()

class IsAdminOrReadOnlyTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdminOrReadOnly()
        self.student = User.objects.create_user(username="student", email="student@test.com", password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", password="password",
                                              is_staff=True)

    def test_read_only_access(self):
        # Safe methods should be allowed for anyone
        for method in SAFE_METHODS:
            request = self.factory.generic(method, '/')
            request.user = self.student
            self.assertTrue(self.permission.has_permission(request, None))

            request.user = None  # Anonymous
            self.assertTrue(self.permission.has_permission(request, None))

    def test_write_access_student(self):
        # Unsafe methods should be denied for student
        for method in ["POST", "PUT", "DELETE"]:
            request = self.factory.generic(method, '/')
            request.user = self.student
            self.assertFalse(self.permission.has_permission(request, None))

    def test_write_access_admin(self):
        # Unsafe methods should be allowed for admin
        for method in ["POST", "PUT", "DELETE"]:
            request = self.factory.generic(method, '/')
            request.user = self.admin
            self.assertTrue(self.permission.has_permission(request, None))
