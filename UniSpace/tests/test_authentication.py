from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from UniSpace.authentication import CustomSessionAuthentication


User = get_user_model()


class CustomSessionAuthenticationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.auth = CustomSessionAuthentication()

    def test_enforce_csrf_returns_none(self):
        request = self.factory.post('/api/test/')
        
        result = self.auth.enforce_csrf(request)
        self.assertIsNone(result)

    def test_no_csrf_exception_raised(self):
        request = self.factory.post('/api/test/')
        
        # Anche senza token CSRF, enforce_csrf non dovrebbe sollevare eccezioni
        try:
            self.auth.enforce_csrf(request)
        except Exception as e:
            self.fail(f"enforce_csrf raised {type(e).__name__}: {e}")

    def test_csrf_disabled_for_all_methods(self):
        methods = ['POST', 'PUT', 'PATCH', 'DELETE']
        
        for method in methods:
            with self.subTest(method=method):
                request = self.factory.generic(method, '/api/test/')
                result = self.auth.enforce_csrf(request)
                self.assertIsNone(result, f"CSRF should be disabled for {method}")

    def test_enforce_csrf_with_different_paths(self):
        paths = ['/api/auth/login/', '/api/spaces/', '/admin/']
        
        for path in paths:
            with self.subTest(path=path):
                request = self.factory.post(path)
                result = self.auth.enforce_csrf(request)
                self.assertIsNone(result, f"CSRF should be disabled for {path}")