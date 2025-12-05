from django.test import SimpleTestCase


class ViewsModuleTest(SimpleTestCase):
    
    def test_import_views_module(self):

        from userProfile import views  

        self.assertIsNotNone(views)