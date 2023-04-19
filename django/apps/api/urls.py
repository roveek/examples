from django.urls import path

from apps import api

urlpatterns = [
    path('v<int:api_version>/order/',
         api.order.view.OrderView.as_view()),
]
