from django.db import migrations

from apps.qa_01 import models


def custom_migration(apps, schema_editor):
    Book: models.Book = apps.get_model('qa_01', 'Book')
    Author: models.Author = apps.get_model('qa_01', 'Author')
    Language: models.Language = apps.get_model('qa_01', 'Language')

    lang_s = Language.objects.get(name__iexact='Суахили')
    books = Book.objects.filter(
        authors__in=[
            Author.objects.get(
                first_name__iexact='Аркадий',
                last_name__iexact='Стругацкий',
            ),
            Author.objects.get(
                first_name__iexact='Борис',
                last_name__iexact='Стругацкий',
            ),
        ]
    ).distinct()
    for book in books:
        book.available_languages.add(lang_s)


class Migration(migrations.Migration):

    dependencies = [
        ('qa_01', '0002_custom_add1'),
    ]

    operations = [
        migrations.RunPython(custom_migration),
    ]
