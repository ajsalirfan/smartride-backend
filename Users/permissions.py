from rest_framework import permissions

class IsVerifiedUser(permissions.BasePermission):
    """
    Allows access only to verified users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_verified

class CanBookRide(permissions.BasePermission):
    """
    Allows access only to users who can book rides.
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.is_verified and 
                request.user.verification_status == 'approved')

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user