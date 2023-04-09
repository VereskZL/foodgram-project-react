from rest_framework import permissions


class AuthorOrAdmin(permissions.BasePermission):
    """
    Пользовательское разрешение, позволяющее просматривать всем,
    добавлять авторизизированным, а редактировать и удалять
    объект авторам, модераторам и админам
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_admin
            or request.user.is_moderator
            or obj.author == request.user
        )
