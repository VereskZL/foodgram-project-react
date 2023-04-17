from rest_framework import permissions


class AuthorOrAdmin(permissions.BasePermission):
    """
    Пользовательское разрешение, позволяющее просматривать всем,
    добавлять авторизизированным, а редактировать и удалять
    объект авторам и админам
    """

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_admin)
