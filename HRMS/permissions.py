from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        # Check if user is authenticated and is admin
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role == "admin"
        )


class IsHR(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role == "hr"
        )


class IsSREmployee(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role == "SR_employee"
        )


class IsJREmployee(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role == "JR_employee"
        )


class IsAdminOrHR(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role in ["admin", "hr"]
        )


class IsSeniorStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role in ["admin", "hr", "SR_employee"]
        )


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'role') and 
            request.user.role in ["admin", "hr", "SR_employee", "JR_employee"]
        )


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        # Check if user exists and has is_authenticated property
        return (
            request.user and 
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated
        )


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user and hasattr(request.user, 'role') and request.user.role == "admin":
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'employee'):
            return obj.employee.id == request.user.id
        elif hasattr(obj, 'empId'):
            return obj.empId.id == request.user.id
        
        return False


class IsActiveEmployee(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            hasattr(request.user, 'status') and 
            request.user.status == "active" and
            hasattr(request.user, 'role')
        )


class AllowAny(BasePermission):
    def has_permission(self, request, view):
        return True


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in ['GET', 'HEAD', 'OPTIONS']