from django.core.exceptions import ValidationError
from django.utils import timezone

from api.decorators import doc
from utils.constants import FORBIDDEN_USERNAME


@doc(f'Запрещает использование имени {FORBIDDEN_USERNAME}')
def validate_username(value):
    """Валидация имени пользователя."""
    if value == FORBIDDEN_USERNAME:
        raise ValidationError(
            f'Использовать имя {FORBIDDEN_USERNAME} '
            'в качестве логина запрещено.'
        )


def validate_year(value):
    """
    Проверяет, что указанный год не превышает текущий.

    Валидатор используется для проверки корректности года в различных моделях
    (например, для года выпуска произведений, публикаций и т.д.).

    Args:
        value (int): Проверяемое значение года.

    Raises:
        ValidationError: Если переданный год больше текущего.

    Returns:
        None: Функция не возвращает значение в случае успешной валидации.
    """
    now = timezone.now().year
    if value > now:
        raise ValidationError(
            f'{value} не может быть больше {now}'
        )
