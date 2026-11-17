from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allow access to staff/admin users (is_staff, user_type=='admin' or superuser).
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and (user.is_staff or getattr(user, 'user_type', '') == 'admin' or user.is_superuser))

class IsSuperAdmin(permissions.BasePermission):
    """
    Allow only superusers.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and user.is_superuser)

class IsFleetManager(permissions.BasePermission):
    """
    Allow users who are marked as admin_profile.department == 'fleet' or staff with role.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        # Try admin_profile relation (AdminUser model)
        admin_profile = getattr(user, 'admin_profile', None)
        if admin_profile and getattr(admin_profile, 'department', '') == 'fleet':
            return True
        # Fallback to staff_member/StaffProfile role check if present
        staff_profile = getattr(user, 'staff_work_profile', None)
        if staff_profile and getattr(staff_profile, 'role', '') in ['fleet_manager', 'rebalancer']:
            return True
        return False

class IsSupportStaff(permissions.BasePermission):
    """
    Allow users in support department.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        admin_profile = getattr(user, 'admin_profile', None)
        if admin_profile and getattr(admin_profile, 'department', '') == 'support':
            return True
        # fallback on role name if available
        if getattr(user, 'user_type', '') == 'staff':
            staff_profile = getattr(user, 'staff_work_profile', None)
            if staff_profile and getattr(staff_profile, 'role', '') == 'dispatcher':
                return True
        return False

# New: view-level required permission checker
class HasAdminPermission(permissions.BasePermission):
    """
    Checks view.required_permission (string) against admin_profile.permissions (list)
    If view.required_permission is not set, falls back to IsAdminUser.
    """
    def has_permission(self, request, view):
        # If no required_permission declared, fall back to IsAdminUser
        required = getattr(view, 'required_permission', None)
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        # superusers bypass
        if user.is_superuser:
            return True
        if not required:
            # fallback to basic admin check
            return bool(user.is_staff or getattr(user, 'user_type', '') == 'admin' or getattr(user, 'admin_profile', None))
        # check admin_profile permissions list safely
        admin_profile = getattr(user, 'admin_profile', None)
        perms = []
        if admin_profile:
            try:
                perms = list(admin_profile.permissions or [])
            except Exception:
                perms = []
        # support staff_work_profile fallback
        staff_profile = getattr(user, 'staff_work_profile', None)
        if staff_profile and hasattr(staff_profile, 'permissions'):
            try:
                perms += list(staff_profile.permissions or [])
            except Exception:
                pass
        return required in perms
