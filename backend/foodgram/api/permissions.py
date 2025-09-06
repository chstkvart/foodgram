from rest_framework import permissions


class ReadOnly(permissions.BasePermission):
    """Разрешает только безопасные методы (GET, HEAD, OPTIONS)."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешает изменение только автору объекта, чтение - всем."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdmin(permissions.BasePermission):
    """Разрешает доступ только администраторам."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешает изменение только владельцу, чтение - всем."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user