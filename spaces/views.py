from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Building, Equipment, Space, Departments
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
    
    # GET /api/spaces/departments
    @action(detail=False, methods=["get"], url_path="departments")
    def departments(self, request):
        departments_list = []
        
        for department_code, department_name in Departments.choices:
            departments_list.append({
                "code": department_code,
                "name": department_name
            })
        
        return Response(departments_list, status=status.HTTP_200_OK)