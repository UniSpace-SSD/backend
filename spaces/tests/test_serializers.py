from django.test import TestCase
from spaces.serializers import SpaceSerializer
from spaces.models import Building, SpaceType

class SpaceSerializerTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="123 Test St")

    def test_valid_serializer(self):
        data = {
            "name": "Room 201",
            "type": SpaceType.ROOM,
            "building_id": self.building.id,
            "floor": 2,
            "capacity": 20
        }
        serializer = SpaceSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_capacity(self):
        data = {
            "name": "Room 202",
            "type": SpaceType.ROOM,
            "building_id": self.building.id,
            "floor": 2,
            "capacity": -1 # Invalid
        }
        serializer = SpaceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("capacity", serializer.errors)

    def test_invalid_floor(self):
        data = {
            "name": "Room 203",
            "type": SpaceType.ROOM,
            "building_id": self.building.id,
            "floor": 200, # Invalid
            "capacity": 20
        }
        serializer = SpaceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("floor", serializer.errors)
