from rest_framework import serializers
from .models import Building, Equipment, Space, SpaceType


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "name", "address", "department"]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["id", "name", "description"]


class SpaceSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=SpaceType.choices)
    building = BuildingSerializer(read_only=True)
    building_id = serializers.PrimaryKeyRelatedField(
        source="building",
        queryset=Building.objects.all(),
        write_only=True,
    )
    equipments = EquipmentSerializer(read_only=True, many=True)
    equipment_ids = serializers.PrimaryKeyRelatedField(
        source="equipments",
        queryset=Equipment.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    department = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Space
        fields = [
            "id",
            "name",
            "type",
            "building",
            "building_id",
            "floor",
            "capacity",
            "equipments",
            "equipment_ids",
            "department",
        ]

    def get_department(self, obj):
        return obj.building.department if obj.building else None

class DepartmentSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()