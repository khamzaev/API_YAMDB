from django.conf import settings
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.filters import TitleFilter
from api.permissions import (AdminModeratorAuthorPermission, IsAdmin,
                             IsAdminUserOrReadOnly)
from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, ReviewSerializer,
                             SignupSerializer, TitleReadSerializer,
                             TitleWriteSerializer, TokenSerializer,
                             UserSerializer)
from reviews.models import Category, Genre, Review, Title
from users.models import User


class BaseModelViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    """
    Набор миксинов для создания, списка и удаления моделей.

    Этот класс объединяет функции создания, списка и удаления моделей
    в одном наборе представлений. Он наследуется от:
    - CreateModelMixin: Обеспечивает создание новых объектов модели.
    - ListModelMixin: Обеспечивает получение списка объектов модели.
    - DestroyModelMixin: Обеспечивает удаление объектов модели.
    - GenericViewSet: Базовый класс представлений.

    Методы:
    - create: Обработка создания нового объекта модели.
    - list: Обработка получения списка объектов модели.
    - destroy: Обработка удаления объекта модели.
    """

    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'
    permission_classes = (IsAdminUserOrReadOnly,)


class CategoryViewSet(BaseModelViewSet):
    """
    API endpoint для работы с категориями произведений.

    Действия:
    - GET /categories/ — список всех категорий
    - GET /categories/{slug}/ — детализация категории
    - POST /categories/ — создание новой категории (только админ)
    - DELETE /categories/{slug}/ — удаление категории (только админ)

    Права доступа:
    - Чтение: доступно без токена
    - Запись: требуется права администратора
    - Удаление: требуется права администратора

    Параметры:
    - search: фильтрация по названию (регистронезависимый поиск)
    - lookup_field: slug (используется в URL вместо id)
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(BaseModelViewSet):
    """
    API endpoint для работы с жанрами произведений.

    Действия:
    - GET /genres/ — список всех жанров
    - GET /genres/{slug}/ — детализация жанра
    - POST /genres/ — создание нового жанра (только админ)
    - DELETE /genres/{slug}/ — удаление жанра (только админ)

    Права доступа:
    - Чтение: доступно без токена
    - Запись: требуется права администратора
    - Удаление: требуется права администратора

    Параметры:
    - search: фильтрация по названию (регистронезависимый поиск)
    - lookup_field: slug (используется в URL вместо id)
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(ModelViewSet):
    """
    API endpoint для работы с произведениями.

    Действия:
    - GET /titles/ — список всех произведений с рейтингом
    - GET /titles/{id}/ — детализация произведения
    - POST /titles/ — создание произведения (только админ)
    - PATCH /titles/{id}/ — частичное обновление (админ/модератор)
    - DELETE /titles/{id}/ — удаление произведения (только админ)

    Особенности:
    - PUT-запросы запрещены (только PATCH)
    - Рейтинг рассчитывается как среднее оценок отзывов
    - Используются разные сериализаторы для чтения и записи

    Права доступа:
    - Чтение: доступно без токена
    - Запись: требуется права администратора/модератора
    - Удаление: требуется права администратора
    """

    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).all().order_by('rating')
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter)
    ordering_fields = ('title_id',)
    filterset_class = TitleFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления отзывами на произведения.

    Действия:
    - GET /titles/{title_id}/reviews/ — список отзывов
    - POST /titles/{title_id}/reviews/ — создать отзыв (аутентиф. пользователи)
    - GET /titles/{title_id}/reviews/{id}/ — детализация отзыва
    - PATCH /titles/{title_id}/reviews/{id}/ — обновить отзыв
    - DELETE /titles/{title_id}/reviews/{id}/ — удалить отзыв

    Правила:
    - Один пользователь — один отзыв на произведение
    - Редактировать/удалять могут: автор, модератор или админ
    - PUT-запросы запрещены (только PATCH)

    Параметры:
    - title_id: ID произведения в URL
    """

    serializer_class = ReviewSerializer

    permission_classes = (IsAuthenticatedOrReadOnly,
                          AdminModeratorAuthorPermission)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title = self.get_title()
        return title.reviews.all()

    def perform_create(self, serializer):
        title = self.get_title()
        serializer.save(author=self.request.user, title=title)

    def get_title(self):
        return get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        )


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления комментариями к отзывам.

    Действия:
    - GET /titles/{title_id}/reviews/{review_id}/comments/ — список
        комментариев
    - POST /titles/{title_id}/reviews/{review_id}/comments/ — создать
        комментарий
    - PATCH /titles/{title_id}/reviews/{review_id}/comments/{id}/ — обновить
    - DELETE /titles/{title_id}/reviews/{review_id}/comments/{id}/ — удалить

    Правила:
    - Редактировать/удалять могут: автор, модератор или админ
    - PUT-запросы запрещены (только PATCH)
    - Привязка к отзыву через review_id в URL

    Параметры:
    - review_id: ID отзыва в URL
    - title_id: ID произведения в URL
    """

    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          AdminModeratorAuthorPermission)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        review = self.get_review()
        serializer.save(author=self.request.user, review=review)

    def get_review(self):
        return get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'),
            title_id=self.kwargs.get('title_id')
        )


class SignupView(APIView):
    """
    Представление для регистрации пользователей и отправки кода подтверждения.

    Разрешает неаутентифицированный доступ. При регистрации:
    - Если пользователь с указанными username/email существует: генерирует
        новый код подтверждения.
    - Если пользователь новый: создает запись пользователя и генерирует код
        потдверждения.
    - Во всех случаях отправляет код подтверждения на email.
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Обрабатывает POST-запрос с данными регистрации.

        Параметры запроса:
        - username (обязательный)
        - email (обязательный)

        Возвращает:
        - 200 OK с username/email при успешной отправке кода
        - 500 при ошибке на стороне сервера
        - 400 при невалидных данных
        """
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
            return Response(
                {
                    'email': serializer.data['email'],
                    'username': serializer.data['username']
                },
                status=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            error_message = (
                str(e) if settings.DEBUG
                else 'Ошибка со стороны клиента'
            )
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            error_message = (
                str(e) if settings.DEBUG
                else 'Ошибка на сервере'
            )
            return Response(
                {'error': error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TokenObtainView(APIView):
    """
    Представление для получения JWT токена после верификации confirmation_code.

    Логика работы:
    1. Принимает username и confirmation_code
    2. Валидирует данные через TokenSerializer
    3. Возвращает JWT токен при успехе
    """

    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Проверяет код подтверждения и выдает токен доступа.

        Параметры запроса:
        - username (обязательный)
        - confirmation_code (обязательный)

        Возвращает:
        - 200 OK с JWT токеном при успешной проверке
        - 400 при неверном коде или отсутствии пользователя
        """
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями через API.

    Требует прав администратора для операций:
    - Просмотр списка/детализации
    - Создание/изменение/удаление пользователей

    Поддерживает:
    - Поиск по username (параметр search)
    - Пагинацию
    - Кастомный эндпоинт /me/ для личных данных
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    pagination_class = PageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def me(self, request):
        """
        Эндпоинт для работы с данными текущего пользователя.

        GET:
        - Возвращает данные аутентифицированного пользователя

        PATCH:
        - Позволяет частичное обновление данных пользователя
        - Запрещает изменение ролей и других привилегированных полей
        - Валидирует входные данные через UserSerializer
        """
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
