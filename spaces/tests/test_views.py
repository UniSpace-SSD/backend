from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from spaces.models import Building, Space, SpaceType
from django.utils import timezone

User = get_user_model()

class SpaceViewSetTest(APITestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="Via 123 Test")
        self.space = Space.objects.create(name="Test Space", building=self.building, capacity=10)

        self.student = User.objects.create_user(username="student", email="student@test.com", date_of_birth=timezone.now(), password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", date_of_birth=timezone.now(), password="password",
                                              is_staff=True)

        self.list_url = reverse('spaces:space-list')
        self.detail_url = reverse('spaces:space-detail', args=[self.space.id])

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
        data = {"name": "Updated Room", "building_id": self.building.id, "capacity": self.space.capacity, "type": self.space.type}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.space.refresh_from_db()
        self.assertEqual(self.space.name, "Updated Room")
