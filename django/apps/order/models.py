from django.db import models

import base


class Order(base.db.CrUpModel):
    """БД-модель заказа"""

    name = models.CharField(
        verbose_name='Наименование', max_length=255,
        blank=False, null=False)

    class Meta:
        db_table = 'orders'
        verbose_name_plural = 'Заказы'
        verbose_name = 'заказ'
