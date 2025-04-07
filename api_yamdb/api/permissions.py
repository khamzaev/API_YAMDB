from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Права доступа для администратора."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )


class AdminModeratorAuthorPermission(permissions.BasePermission):
    """
    Предоставляет доступ в объекту при определенных условиях.

    1. Запрос является безопасным (GET, HEAD, OPTIONS)
    2. Пользователь - автор объекта
    3. Пользователь имеет роль администратора
    4. Пользователь имеет роль модератора
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверка разрешений для конкретного объекта.

        Разрешает доступ:
        - Для чтения данных всем пользователям
        - Для записи только автору/администратору/модератору
        """
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_admin
            or request.user.is_moderator
        )


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Предоставляет доступ в объекту при определенных условиях.

    1. Запрос использует безопасные методы (GET, HEAD, OPTIONS)
    2. Пользователь аутентифицирован и имеет статус администратора

    Разрешения:
    - Чтение: разрешено всем пользователям
    - Запись: только администраторам
    """

    def has_permission(self, request, view):
        """
        Проверяет разрешения на уровне всего запроса.

        Разрешает доступ:
        - Используется безопасный HTTP-метод
        - ИЛИ пользователь аутентифицирован и является администратором
        """
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated and request.user.is_admin
        )
