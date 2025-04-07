import os

import pandas as pd
from django.core.management.base import BaseCommand

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User

DATA_DIR = 'static/data'


class Command(BaseCommand):
    help = "Загружает данные из файлов CSV в базу данных"

    def _load_csv(self, file_name):
        """Загрузка CSV-файла с обработкой ошибок."""
        file_path = os.path.join(DATA_DIR, file_name)
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(
                f'Файл {file_name} не найден в директории {DATA_DIR}'))
            return None
        return pd.read_csv(file_path)

    def _process_category(self, row):
        data = row.to_dict()
        Category.objects.get_or_create(**data)

    def _process_genre(self, row):
        data = row.to_dict()
        Genre.objects.get_or_create(**data)

    def _process_title(self, row):
        data = row.to_dict()
        category = Category.objects.get(id=data.pop('category'))
        Title.objects.get_or_create(category=category, **data)

    def _process_genre_title(self, row):
        data = row.to_dict()
        title = Title.objects.get(id=data['title_id'])
        genre = Genre.objects.get(id=data['genre_id'])
        title.genre.add(genre)

    def _process_user(self, row):
        data = row.to_dict()
        for field in ['bio', 'first_name', 'last_name']:
            if pd.isna(data.get(field)):
                data[field] = ''
        User.objects.get_or_create(**data)

    def _process_review(self, row):
        data = row.to_dict()
        title = Title.objects.get(id=data.pop('title_id'))
        author = User.objects.get(id=data.pop('author'))
        Review.objects.get_or_create(title=title, author=author, **data)

    def _process_comment(self, row):
        data = row.to_dict()
        review = Review.objects.get(id=data.pop('review_id'))
        author = User.objects.get(id=data.pop('author'))
        Comment.objects.get_or_create(review=review, author=author, **data)

    def _load_data(self, file_name, processor, model_name):
        """Общая логика загрузки данных для разных моделей."""
        self.stdout.write(f'Загрузка {model_name}...')
        data = self._load_csv(file_name)
        if data is None:
            return
        processor_func = getattr(self, f'_process_{processor}')
        for _, row in data.iterrows():
            processor_func(row)
        self.stdout.write(self.style.SUCCESS(
            f'Загружено {len(data)} {model_name}.'))

    def handle(self, *args, **options):
        self.stdout.write('Начинаем загрузку данных...')
        load_sequence = [
            ('category.csv', 'category', 'категорий'),
            ('genre.csv', 'genre', 'жанров'),
            ('titles.csv', 'title', 'произведений'),
            ('genre_title.csv', 'genre_title', 'связей жанров и произведений'),
            ('users.csv', 'user', 'пользователей'),
            ('review.csv', 'review', 'отзывов'),
            ('comments.csv', 'comment', 'комментариев'),
        ]
        for file_name, processor, model_name in load_sequence:
            self._load_data(file_name, processor, model_name)
        self.stdout.write(self.style.SUCCESS('Загрузка данных завершена.'))
