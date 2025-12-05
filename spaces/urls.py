from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "spaces"

router = DefaultRouter()
router.register("buildings", views.BuildingViewSet, basename="building")
router.register("spaces", views.SpaceViewSet, basename="space")
router.register("equipments", views.EquipmentViewSet, basename="equipment")

urlpatterns = [
    path("", include(router.urls)),
]
