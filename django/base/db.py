import pydantic
from django.db import models


def admin_display(
        desc: str = None, order: str = None,
        allow_tags: bool = None, boolean: bool = None):

    def decorator(func: typing.Callable):

        if desc is not None:
            func.short_description = desc
        if order is not None:
            func.admin_order_field = order
        if allow_tags is not None:
            func.allow_tags = allow_tags
        if boolean is not None:
            func.boolean = boolean

        return func

    return decorator


class BaseDbDto(pydantic.BaseModel):
    id: int = None

    class Config:
        extra = pydantic.Extra.ignore
        orm_mode = True
        validate_assignment = True
        underscore_attrs_are_private = True


class CrUpModel(models.Model):
    """Базовый класс модели с полями created_at и modified_at"""

    created_at = models.DateTimeField(
        verbose_name='Запись создана',
        help_text='Дата создания (добавления) записи в БД',
        auto_now_add=True)
    modified_at = models.DateTimeField(
        verbose_name='Запись изменена',
        help_text='Дата последнего изменения записи в БД',
        auto_now=True)

    class Meta:
        abstract = True
