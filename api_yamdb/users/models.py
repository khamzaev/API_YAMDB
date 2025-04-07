from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import Truncator

from api.validators import validate_username
from users.service import get_max_length
from utils.constants import (ALLOWED_SYMBOLS_FOR_USERNAME, EMAIL_LENGTH,
                             LIMIT_OF_SYMBOLS, USERNAME_LENGTH)


class User(AbstractUser):
    """
    Расширенная модель пользователя с расширенными полями и ролями.

    Дополнительные поля:
    - bio: Текстовая биография пользователя.
    - role: Для работы с ролями пользователей.
    - confirmation_code: Код подтверждения, для получения JWT токена.

    Свойства:
    - is_admin: Возвращает True, если пользователь является администратором
        или суперпользователем.
    - is_moderator: Возвращает True, если пользователь является модератором.
    """

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLE_CHOICES = (
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    )
    username = models.CharField(
        'Логин',
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=ALLOWED_SYMBOLS_FOR_USERNAME,
                message='Недопустимые символы в имени пользователя.'
            ),
            validate_username
        ]
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=EMAIL_LENGTH,
        unique=True
    )
    bio = models.TextField('Биография', blank=True)
    role = models.CharField(
        'Роль',
        max_length=get_max_length(ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=USER
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает ограниченное строковое представление пользователя."""
        return Truncator(self.username).words(LIMIT_OF_SYMBOLS)

    @property
    def is_admin(self):
        """Определяет, является ли пользователь администратором."""
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        """Определяет, является ли пользователь модератором."""
        return self.role == self.MODERATOR
