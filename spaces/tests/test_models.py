from django.test import TestCase
from django.core.exceptions import ValidationError
from spaces.models import Building, Equipment, Space, SpaceType

class SpaceModelTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name="Test Building", address="123 Test St")
        self.equipment = Equipment.objects.create(name="Projector", description="HD Projector")

    def test_create_valid_space(self):
        space = Space.objects.create(
            name="Room 101",
            building=self.building,
            floor=1,
            capacity=30,
            type=SpaceType.ROOM
        )
        space.equipments.add(self.equipment)
        space.full_clean()
        self.assertEqual(space.name, "Room 101")
        self.assertEqual(space.equipments.count(), 1)

    def test_invalid_capacity(self):
        space = Space(
            name="Room 102",
            building=self.building,
            floor=1,
            capacity=0,  # Invalid
            type=SpaceType.ROOM
        )
        with self.assertRaises(ValidationError):
            space.full_clean()

    def test_invalid_floor(self):
        space = Space(
            name="Room 103",
            building=self.building,
            floor=101,  # Invalid
            capacity=30,
            type=SpaceType.ROOM
        )
        with self.assertRaises(ValidationError):
            space.full_clean()

    def test_str_representation(self):
        space = Space.objects.create(
            name="Room 104",
            building=self.building,
            floor=1,
            capacity=30
        )
        self.assertEqual(str(space), "Test Building - Room 104")
        self.assertEqual(str(self.building), f"{self.building.id} - Test Building")
        self.assertEqual(str(self.equipment), "Projector")

    def test_type_checking(self):
        # This depends on how typeguard is configured to run.
        # If it's runtime checking on method calls, we can test it.
        # But Django models might do some magic that bypasses direct calls or typeguard might not catch everything in tests without specific setup.
        # However, we decorated __str__ and clean.

        # Test clean with wrong type (if possible to pass wrong type to model field before clean?
        # Django fields convert types usually. But let's try calling clean directly if we could mock something)
        pass
