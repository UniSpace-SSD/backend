from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from spaces.models import Building, Space, SpaceType, Departments
from django.utils import timezone

from dateutil.relativedelta import relativedelta


User = get_user_model()

class SpaceViewSetTest(APITestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="Via 123 Test")
        self.space = Space.objects.create(name="Test Space", building=self.building, capacity=10)

        self.student = User.objects.create_user(
            username="student", 
            email="student@test.com", 
            date_of_birth=timezone.now().date() - relativedelta(years=18), 
            password="password"
        )
        self.admin = User.objects.create_user(
            username="admin", 
            email="admin@test.com", 
            date_of_birth=timezone.now().date() - relativedelta(years=18), 
            password="password",
            is_staff=True
        )

        self.list_url = reverse('spaces:space-list')
        self.detail_url = reverse('spaces:space-detail', args=[self.space.id])
        self.departments_url = reverse('spaces:space-departments')

    def test_list_spaces_public(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_space_student(self):
        self.client.force_authenticate(user=self.student)
        data = {
            "name": "New Room",
            "building_id": self.building.id,
            "capacity": 20,
            "type": SpaceType.ROOM
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_space_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "New Room",
            "building_id": self.building.id,
            "capacity": 20,
            "type": SpaceType.ROOM
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_space_student(self):
        self.client.force_authenticate(user=self.student)
        data = {"name": "Updated Room"}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_space_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Updated Room", 
            "building_id": self.building.id, 
            "capacity": self.space.capacity, 
            "type": self.space.type
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.space.refresh_from_db()
        self.assertEqual(self.space.name, "Updated Room")

    # Test per l'action departments (copre le linee 42-46)
    def test_list_departments(self):
        response = self.client.get(self.departments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica che la risposta contenga tutti i dipartimenti
        self.assertEqual(len(response.data), len(Departments.choices))
        
        # Verifica la struttura dei dati
        for dept in response.data:
            self.assertIn('code', dept)
            self.assertIn('name', dept)
        
        # Verifica che i codici dei dipartimenti siano corretti
        codes = [dept['code'] for dept in response.data]
        expected_codes = [code for code, _ in Departments.choices]
        self.assertEqual(codes, expected_codes)