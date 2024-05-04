from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    """
    Allows access only to users who have verified their email.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.email_verified


class IsNotDeleted(BasePermission):
    """
        Allows access only to users who are not marked as deleted.
    """
    def has_permission(self, request, view):
        # Check if the user exists and is not marked as deleted
        return request.user and request.user.is_authenticated and not request.user.is_deleted
