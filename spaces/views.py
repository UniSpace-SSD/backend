# spaces/views.py
from rest_framework import viewsets, permissions
from .models import Building, Equipment, Space
from .serializers import (
    BuildingSerializer,
    EquipmentSerializer,
    SpaceSerializer,
)

# /api/spaces/buildings/
class BuildingViewSet(viewsets.ModelViewSet):

    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]


# /api/spaces/equipments/
class EquipmentViewSet(viewsets.ModelViewSet):

    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put"]


# /api/spaces/spaces/
class SpaceViewSet(viewsets.ModelViewSet):

    queryset = Space.objects.select_related("building").prefetch_related("equipments")
    serializer_class = SpaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]