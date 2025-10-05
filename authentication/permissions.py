from rest_framework import permissions

class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow only 'Teacher' or 'HOD/Admin' users to access a view.
    """
    def has_permission(self, request, view):
        # Allow read-only access for anyone (GET requests) but restrict POST/PATCH/DELETE
        # For this view, we'll require a specific role for all methods
        return request.user.role in ['Teacher', 'HOD/Admin']