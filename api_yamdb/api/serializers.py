from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from api.validators import validate_username
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User
from utils.constants import (ALLOWED_SYMBOLS_FOR_USERNAME, EMAIL_LENGTH,
                             MAX_SCORE, MIN_SCORE, USERNAME_LENGTH)


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Category.

    Предоставляет сериализацию и десериализацию объектов категорий.
    Используется для отображения и создания категорий в API.
    """

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Genre.

    Предоставляет сериализацию и десериализацию объектов жанров.
    Используется для отображения и создания жанров в API.
    """

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class ReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Review.

    Обеспечивает создание и получение отзывов для произведений.
    Реализует проверку оценки и уникальности отзыва
    от одного пользователя для каждого произведения.
    """

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    score = serializers.IntegerField()

    class Meta:
        fields = ['id', 'text', 'author', 'score', 'pub_date']
        model = Review

    def validate_score(self, value):
        """
        Проверяет, что оценка находится в заданном диапазоне.

        Args:
            value (int): Значение оценки

        Returns:
            int: Корректное значение оценки

        Raises:
            ValidationError: Если оценка выходит за пределы диапазона
        """
        if not (MIN_SCORE <= value <= MAX_SCORE):
            raise serializers.ValidationError(
                f'Оценка должна быть от {MIN_SCORE} до {MAX_SCORE}!'
            )
        return value

    def validate(self, data):
        """
        Проверяет, что пользователь не оставит более 1 отзыва на произведение.

        Args:
            data (dict): Данные для валидации

        Returns:
            dict: Проверенные данные

        Raises:
            ValidationError: Если пользователь уже оставил отзыв на это
                произведение
        """
        request = self.context['request']
        author = request.user
        title_id = self.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if (
                request.method == 'POST'
                and Review.objects.filter(title=title, author=author).exists()
        ):
            raise ValidationError('Может существовать только один отзыв!')
        return data


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Comment.

    Обеспечивает создание и получение комментариев к отзывам.
    Автоматически связывает комментарий с его автором и соответствующим
        отзывом.
    """

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = ['id', 'text', 'author', 'pub_date']
        model = Comment


class TitleReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения объектов модели Title.

    Используется для получения информации о произведениях.
    Включает вложенные данные о категории, жанрах и рейтинге.
    """

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(
        read_only=True,
        many=True
    )
    rating = serializers.IntegerField(read_only=True, default=MIN_SCORE)

    class Meta:
        fields = '__all__'
        model = Title


class TitleWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи объектов модели Title.

    Используется при создании и обновлении произведений.
    Позволяет указывать категорию и жанры по их slug-идентификаторам.
    """

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True,
        allow_empty=False
    )

    class Meta:
        fields = '__all__'
        model = Title

    def to_representation(self, value):
        """
        Переопределяет стандартное представление данных при сериализации.

        Использует TitleReadSerializer для преобразования объекта в формат,
        идентичный GET-запросам.
        """
        return TitleReadSerializer(value, context=self.context).data


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.

    Используется для сериализации данных пользователя, включая поля:
    username, email, first_name, last_name, bio и role.
    """

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and not request.user.is_admin:
            self.fields['role'].read_only = True


class SignupSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации пользователей, отправки кода подтверждения.

    Обрабатывает валидацию email и username:
    - Проверяет соответствие username паттерну ALLOWED_SYMBOLS_FOR_USERNAME
    - Запрещает использование username 'me'
    - Контролирует уникальность связки email/username

    Методы:
    - validate: Кастомная проверка на конфликт email/username с существующими
        пользователями
    - create: Создает или обновляет пользователя, генерирует код подтверждения
    - send_confirmation_email: Отправляет код на email пользователя

    Исключения:
    - ValidationError: При конфликте данных или ошибке отправки email
    """

    email = serializers.EmailField(max_length=EMAIL_LENGTH)
    username = serializers.CharField(
        max_length=USERNAME_LENGTH,
        validators=[
            RegexValidator(regex=ALLOWED_SYMBOLS_FOR_USERNAME),
            validate_username
        ]
    )

    def validate(self, data):
        """
        Проверяет уникальность связки email/username.

        Args:
            data (dict): Входные данные (email и username)

        Returns:
            dict: Валидированные данные

        Raises:
            ValidationError: Если:
                - email занят другим username
                - username занят другим email
        """
        email = data.get('email')
        username = data.get('username')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if user.username != username:
                raise serializers.ValidationError(
                    {'email': 'Email уже занят'}
                )
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.email != email:
                raise serializers.ValidationError(
                    {'username': 'Username уже занят'}
                )
        return data

    def create(self, validated_data):
        """
        Создает или обновляет пользователя.

        Логика:
        1. Ищет пользователя по email и username
        2. Если не найден - создает нового с is_active=False
        3. Генерирует новый confirmation_code
        4. Отправляет код на email

        Args:
            validated_data (dict): Валидные данные (email, username)

        Returns:
            User: Созданный/обновленный пользователь
        """
        user, _ = User.objects.get_or_create(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        confirmation_code = default_token_generator.make_token(user)
        self.send_confirmation_email(user, confirmation_code)
        return user

    def send_confirmation_email(self, user, confirmation_code):
        """
        Отправляет письмо с кодом подтверждения.

        Args:
            user (User): Объект пользователя для отправки

        Raises:
            ValidationError: При ошибке отправки email
        """

        send_mail(
            subject='Код подтверждения',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )


class TokenSerializer(serializers.Serializer):
    """
    Сериализатор для получения токена аутентификации.

    Требует поля username и confirmation_code. Проверяет, что confirmation_code
    соответствует коду, хранящемуся для пользователя, и при успешной валидации
    возвращает токен и username.
    """

    username = serializers.CharField(max_length=USERNAME_LENGTH)
    confirmation_code = serializers.CharField()

    def validate(self, data):
        """Основная логика валидации кода подтверждения."""
        user = get_object_or_404(User, username=data['username'])
        if not default_token_generator.check_token(
            user,
            data['confirmation_code']
        ):
            raise serializers.ValidationError(
                {'confirmation_code': 'Код подтверждения обязателен.'}
            )
        return {
            'token': str(AccessToken.for_user(user)),
            'username': user.username,
        }
