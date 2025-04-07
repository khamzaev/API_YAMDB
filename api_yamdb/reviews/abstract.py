from django.db import models
from django.utils.text import Truncator

from users.models import User
from utils.constants import LIMIT_OF_SYMBOLS, NAME_LIMIT


class BaseCategoryGenreModel(models.Model):
    """Абстрактная модель для жанров и категорий."""

    name = models.CharField(verbose_name='Название',
                            max_length=NAME_LIMIT,
                            unique=True)
    slug = models.SlugField(verbose_name='Уникальный слаг', unique=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return Truncator(self.name).words(LIMIT_OF_SYMBOLS)


class BaseReviewCommentModel(models.Model):
    """Абстрактная модель для отзывов и комментариев."""

    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True
        ordering = ['pub_date']

    def __str__(self):
        """Возвращает ограниченное строковое представление текста."""
        return Truncator(self.text).words(LIMIT_OF_SYMBOLS)
