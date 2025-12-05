from rest_framework import viewsets
from .models import Building, Equipment, Space
from .serializers import (
    BuildingSerializer,
    EquipmentSerializer,
    SpaceSerializer,
)
from .permissions import IsAdminOrReadOnly

class BuildingViewSet(viewsets.ModelViewSet):

    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "put", "delete"]

class EquipmentViewSet(viewsets.ModelViewSet):

    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "put"]

class SpaceViewSet(viewsets.ModelViewSet):

    queryset = Space.objects.select_related("building").prefetch_related("equipments")
    serializer_class = SpaceSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "put", "delete"]