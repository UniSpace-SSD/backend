from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "reservations"

router = DefaultRouter()
router.register("reservations", views.ReservationViewSet, basename="reservation")

urlpatterns = [
    path("", include(router.urls)),
]