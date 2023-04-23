## Вопросы с собеседований

####Как можно улучшить django-код?
```python
for site in Site.objects.all():
    print(site.user.email)
```
Можно уменьшить количество запросов в БД:
```python
for site in Site.objects.select_related('user'):
    print(site.user.email)
```

---

####Как можно улучшить django-код?
```python
for u in User.objects.all(): 
    print ([g.name for g in u.groups.all()])
```
Можно уменьшить количество запросов в БД.
А модель django-пользователя лучше получать с помощью get_user_model().  
```python
user_model = django.contrib.auth.get_user_model()
queryset = user_model.objects.prefetch_related('groups')
for u in queryset:
    print([g.name for g in u.groups.all()])
```

---
