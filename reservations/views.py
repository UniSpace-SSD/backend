from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Reservation
from .serializers import ReservationSerializer


class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, obj: Reservation):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        return obj.created_by_id == request.user.id


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        qs = Reservation.objects.select_related("created_by")
        if user.is_staff:
            return qs
        return qs.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


    @action(detail=True, methods=["put"])
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

    @action(detail=True, methods=["put"])
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
