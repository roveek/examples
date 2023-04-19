from django import http

from apps import api


class OrderView(api.base.view.BaseApiView):

    def get_v1(self, request: http.HttpRequest) -> http.HttpResponse:
        return api.order.v1.get.controller.ViewController(request).handle_request()
