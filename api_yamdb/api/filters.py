from django_filters import rest_framework as filters

from reviews.models import Title


class TitleFilter(filters.FilterSet):
    """
    Набор фильтров для модели Title.

    Предоставляет возможность фильтрации произведений по нескольким параметрам:
    - category: поиск по slug категории (нечувствительный к регистру)
    - genre: поиск по slug жанра (нечувствительный к регистру)
    - name: поиск по названию произведения (нечувствительный к регистру)
    - year: фильтрация по году выпуска произведения

    Используется в API для обеспечения поиска и фильтрации списка произведений
    по запросу пользователя.
    """

    category = filters.CharFilter(
        field_name='category__slug',
        lookup_expr='icontains'
    )
    genre = filters.CharFilter(
        field_name='genre__slug',
        lookup_expr='icontains'
    )
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    class Meta:
        model = Title
        fields = ['category', 'genre', 'name', 'year']
