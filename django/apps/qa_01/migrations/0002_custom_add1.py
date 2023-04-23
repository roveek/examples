from django.db import migrations

from apps.qa_01 import models


def custom_migration(apps, schema_editor):
    Book: models.Book = apps.get_model('qa_01', 'Book')
    Author: models.Author = apps.get_model('qa_01', 'Author')
    Language: models.Language = apps.get_model('qa_01', 'Language')

    author_as = Author.objects.create(
        first_name='Аркадий',
        last_name='Стругацкий',
        birth_date='1925-08-28',
    )
    author_sb = Author.objects.create(
        first_name='Борис',
        last_name='Стругацкий',
        birth_date='1933-04-15',
    )
    lang_ru = Language.objects.create(
        name='Русский',
    )
    lang_en = Language.objects.create(
        name='Английский',
    )
    Language.objects.create(
        name='Суахили',
    )

    book1 = Book.objects.create(
        title='Трудно быть богом',
    )
    book1.authors.add(author_as, author_sb)
    book1.available_languages.add(lang_ru, lang_en)

    book2 = Book.objects.create(
        title='Пикник на обочине',
    )
    book2.authors.add(author_as, author_sb)
    book2.available_languages.add(lang_ru, lang_en)


class Migration(migrations.Migration):

    dependencies = [
        ('qa_01', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(custom_migration),
    ]
