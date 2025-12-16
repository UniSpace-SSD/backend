from rest_framework import permissions
from .models import Reservation

class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Reservation):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        return (obj.created_by_id == request.user.id or 
               (obj.space.building.department == request.user.department and request.user.role == 'professor' and obj.created_by.role == 'student') or
               request.user.is_superuser)