from django.contrib import admin

from api_yamdb.settings import ADMIN_EMPTY_VALUE_DISPLAY
from reviews.models import Category, Comment, Genre, Review, Title

empty_value_display = ADMIN_EMPTY_VALUE_DISPLAY


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Административная панель для модели Review."""

    list_display = (
        'title',
        'text',
        'author',
        'score',
    )
    search_fields = ('^pub_date',)
    list_filter = ('pub_date',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Административная панель для модели Comment."""

    list_display = (
        'review',
        'text',
        'author',
        'pub_date',
    )
    search_fields = (
        '^review__text',
        '^review__author__username',
        '^author__username',
        '^text',
    )
    list_filter = ('review',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Административная панель для управления категориями."""

    list_display = ('name', 'slug')
    search_fields = ('^name', '^slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Административная панель для управления жанрами."""

    list_display = ('name', 'slug')
    search_fields = ('^name', '^slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('name',)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    """Административная панель для управления произведениями."""

    list_display = (
        'name',
        'year',
        'category',
        'description',
        'get_genres'
    )
    list_editable = ('category',)
    search_fields = ('^name', '^year', '^category__name', '^genre__name')
    list_filter = ('category', 'genre')
    filter_horizontal = ('genre',)

    def get_queryset(self, request):
        """Возвращает QuerySet с предварительной выборкой связанных жанров."""
        return super().get_queryset(request).prefetch_related('genre')

    @admin.display(description='Жанры')
    def get_genres(self, obj):
        """Возвращает строку с перечислением жанров через запятую."""
        genres = obj.genre.all().order_by('name')
        return ', '.join([genre.name for genre in genres]) if genres else '---'
