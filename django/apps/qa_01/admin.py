from django.contrib import admin

from apps.qa_01.models import Author
from apps.qa_01.models import Book
from apps.qa_01.models import Language


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        lambda o: ', '.join(map(str, o.authors.all())),
        lambda o: ', '.join(map(str, o.available_languages.all())),
    ]


@admin.register(Author)
class BookAdmin(admin.ModelAdmin):
    pass


@admin.register(Language)
class BookAdmin(admin.ModelAdmin):
    pass
