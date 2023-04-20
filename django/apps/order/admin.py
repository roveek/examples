from django.contrib import admin

from apps import order


@admin.register(order.models.Order)
class OrderAdmin(admin.ModelAdmin):
    pass
