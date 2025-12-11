from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404

from userProfile.models import UserProfile

from .models import Reservation
from .serializers import ReservationSerializer
from .permissions import IsOwnerOrStaff
from spaces.models import Space 


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    http_method_names = ["get", "post", "put", "patch"]

    def get_queryset(self):
        user = self.request.user
        qs = Reservation.objects.select_related("created_by", "space")
        if user.is_staff:
            return qs
        return qs.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(auto_schema=None) 
    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "PATCH non disponibile su questa risorsa."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["patch"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        try:
            reservation.cancel(request.user)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.save()
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["patch"])
    def confirm(self, request, pk=None):
        reservation = self.get_object()
        try:
            reservation.confirm(request.user)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.save()
        return Response(self.get_serializer(reservation).data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        user = request.user
        if user.is_staff or user.is_superuser:
            return Response(
                {"detail": "Admin can't access their reservations."},
                status=status.HTTP_403_FORBIDDEN
            )

        qs = self.get_queryset().filter(created_by=request.user)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # GET /api/reservations/space/{space_id}
    @action(detail=False, methods=["get"], url_path="space/(?P<space_id>[^/.]+)")
    def by_space(self, request, space_id=None):
        user = request.user

        space = get_object_or_404(Space, id=space_id)

        qs = Reservation.objects.filter(space=space).select_related("created_by", "space")

        # STAFF / SUPERUSER: vedono tutto
        if user.is_staff or user.is_superuser:
            pass  # nessun filtro aggiuntivo
        # PROFESSOR: tutte le reservation dello spazio ma solo se del proprio dipartimento
        elif getattr(user, "role", None) in (UserProfile.Role.PROFESSOR, "professor"):
            if getattr(user, "department", None) != getattr(space.building, "department", None):
                return Response(
                    {"detail": "Can't visualize reservations for a space that does not belong to your department."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            qs = qs.filter(created_by=user)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)