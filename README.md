# YaMDb — API для отзывов на произведения

Платформа для сбора и управления отзывами пользователей на различные произведения (фильмы, книги, музыку).

## Технологический стек

### Бэкенд
- **Язык**: Python 3.9+
- **Фреймворк**: Django 3.2+ + Django REST Framework
  - ORM для работы с БД
  - JWT-аутентификация
  - REST API с OpenAPI 3.0 документацией
  - Админ-панель
  - Пагинация и фильтрация
  - Валидация данных
  - Ролевая модель доступа
- **База данных**: SQLite

## Особенности проекта

### Основные функции
- Отзывы и оценки:
  - Пользователи могут оставлять отзывы и ставить оценки произведениям (1-10)
  - Средний рейтинг рассчитывается автоматически
- Гибкая система ролей:
  - Аноним: только чтение
  - Пользователь: CRUD для своих отзывов/комментариев
  - Модератор: управление любым контентом
  - Админ: полный контроль через API
- Система комментариев с модерацией
  - Комментарии к отзывам с возможностью редактирования
- Управление контентом:
  - Категории (Книги, Фильмы и т.д.)
  - Жанры (Драма, Комикс и т.д.)
  - Поиск по названию/году/жанру

### Безопасность
- JWT-токены (access/refresh)
- Защита эндпоинтов по ролям
- Валидация данных на уровне API

## Установка

1. Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/khamzaev/API_YAMDB.git
```
```bash
cd api_yamdb
```

2. Создать и активировать виртуальное окружение:

```bash
python -m venv env
```
```bash
source env/bin/activate  # Linux
source env/scripts/activate  # Windows
```

3. Установить зависимости:

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```

4. Выполнить миграции:

```bash
python manage.py migrate
```

5. Загрузить данные из csv файлов в бд:

```bash
python manage.py import_csv
```

6. Запустить проект:

```bash
python manage.py runserver
```

## Основные эндпоинты API


| Метод  | Путь                         | Описание                     | Доступ         |
|--------|------------------------------|------------------------------|----------------|
| GET    | `redoc/          `           | Документация проекта         | Все            |
| POST   | `api/v1/auth/signup/`        | Регистрация по email         | Все            |
| POST   | `api/v1/auth/token/`         | Получение JWT-токена         | Все            |
| GET    | `api/v1/titles/`             | Список произведений          | Все            |
| POST   | `api/v1/titles/{id}/reviews/`| Создать отзыв                | Аутентиф.      |
| PATCH  | `api/v1/users/me/`           | Обновить профиль             | Владелец       |

### Успешные ответы на запросы

1. POST /api/v1/auth/signup/

```json
{
"email": "string",
"username": "string"
}
```

2. POST /api/v1/auth/token/

```json
{
"token": "string"
}
```

3. GET /api/v1/titles/

```json
{
"count": 0,
"next": "string",
"previous": "string",
"results": [
{}
]
}
```

4. POST /api/v1/titles/1/reviews/

```json
{
"id": 0,
"text": "string",
"author": "string",
"score": 1,
"pub_date": "2019-08-24T14:15:22Z"
}
```

5. PATCH /api/v1/users/me/

```json
{
"username": "^w\\Z",
"email": "user@example.com",
"first_name": "string",
"last_name": "string",
"bio": "string",
"role": "user"
}
```

## Модели данных

```python
class User(AbstractUser):
    email = models.EmailField('Электронная почта', max_length=254, unique=True)
    bio = models.TextField('Биография', blank=True)
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='user')
    confirmation_code = models.CharField('Код подтверждения', max_length=16, blank=True)
    ...другие поля

class Title(models.Model):
    name = models.CharField('название', max_length=200, db_index=True)
    year = models.IntegerField('год', validators=(validate_year, ))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, verbose_name='категория', null=True, blank=True)
    ... другие поля

class Review(models.Model):
    title = models.ForeignKey(Title, on_delete=models.CASCADE, verbose_name='произведение')
    text = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='автор', null=True)
    score = models.IntegerField('оценка', validators=(MinValueValidator(1), MaxValueValidator(10))),
    ... другие поля
```

## Производительность

    Оптимизированные SQL-запросы через Django ORM

    Пагинация по умолчанию (10 элементов на странице)

    # Кэширование частых запросов (Redis в планах)

## Авторы
- [Андрей Головушкин / Andrey Golovushkin](https://github.com/Frenky19)

- [Джамал Хамзаев](https://github.com/khamzaev)

- [Мария Ковалева / Maria Kovaleva](https://github.com/Mary-Kovaleva)