from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from .models import Reservation
from .serializers import ReservationSerializer
from .permissions import IsOwnerOrStaff

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    http_method_names = ["get", "post", "put", "patch"]

    def get_queryset(self):
        user = self.request.user
        qs = Reservation.objects.select_related("created_by")
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
        qs = self.get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
