from django.db import models


class Author(models.Model):
    last_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=200)
    birth_date = models.DateField()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        db_table = 'qa-01_authors'


class Language(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.name)

    class Meta:
        db_table = 'qa-01_languages'


class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author)
    available_languages = models.ManyToManyField(Language)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'qa_01_books'
