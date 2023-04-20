from django.conf import settings
from django.db import models

import base


class Order(base.db.CrUpModel):
    """БД-модель заказа"""

    name = models.CharField(
        verbose_name='Наименование', max_length=255,
        blank=False, null=False)
    user = models.ForeignKey(
        verbose_name='Пользователь',
        to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        default=None, blank=True, null=True)

    class Meta:
        db_table = 'orders'
        verbose_name_plural = 'Заказы'
        verbose_name = 'заказ'
