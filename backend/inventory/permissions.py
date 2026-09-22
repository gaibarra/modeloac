from rest_framework.permissions import BasePermission, SAFE_METHODS
class OperationalPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated: return False
        if request.method in SAFE_METHODS: return True
        if user.is_superuser or user.groups.filter(name='Administración').exists(): return True
        if user.groups.filter(name='Mantenimiento').exists():
            return getattr(view,'resource_name','') == 'work-orders'
        return False
