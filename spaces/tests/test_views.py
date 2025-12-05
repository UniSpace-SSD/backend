from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from spaces.models import Building, Space, SpaceType

User = get_user_model()

class SpaceViewSetTest(APITestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="123 Test St")
        self.space = Space.objects.create(name="Test Room", building=self.building, capacity=10)

        self.student = User.objects.create_user(username="student", email="student@test.com", password="password")
        self.admin = User.objects.create_user(username="admin", email="admin@test.com", password="password",
                                              is_staff=True)

        # Assuming standard router URLs
        self.list_url = reverse('space-list')
        self.detail_url = reverse('space-detail', args=[self.space.id])

    def test_list_spaces_public(self):
        # Authenticated user can list
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_space_student(self):
        # Student cannot create
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
        # Admin can create
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
        # Student cannot update
        self.client.force_authenticate(user=self.student)
        data = {"name": "Updated Room"}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_space_admin(self):
        # Admin can update
        self.client.force_authenticate(user=self.admin)
        data = {"name": "Updated Room"}
        response = self.client.post(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.space.refresh_from_db()
        self.assertEqual(self.space.name, "Updated Room")
