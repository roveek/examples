from django import http

import apps
from apps import api


class OrderView(api.base.view.BaseApiView):

    def get_v1(self, request: http.HttpRequest) -> http.HttpResponse:
        queryset = apps.qa_01.models.Book.objects.filter(
            authors__in=[
                apps.qa_01.models.Author.objects.get(
                    first_name__iexact='Аркадий',
                    last_name__iexact='Стругацкий',
                ),
                apps.qa_01.models.Author.objects.get(
                    first_name__iexact='Борис',
                    last_name__iexact='Стругацкий',
                ),
            ]
        ).distinct()
        return http.HttpResponse(', '.join(map(str, queryset)))
        # return api.order.v1.get.controller.ViewController(request).handle_request()
