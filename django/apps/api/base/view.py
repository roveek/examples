"""Базовые классы view и его контроллера

View вызывает метод обработки контроллера, возвращает результат, если всё ок,
ловит исключения и возвращает соответствующие им http-ответы.
"""

import abc
import logging
import typing

import pydantic
from django import http
from django import views

import base

log = logging.getLogger(__name__)


class BaseApiView(views.View):

    @base.tools.json_response
    def get(self, request: http.HttpRequest, api_version: int, *args, **kwargs):
        try:
            return getattr(self, f'get_v{int(api_version)}')(request, *args, **kwargs)
        except (AttributeError, ValueError) as e:
            return base.web.BaseViewError(status=404).add(f'{api_version} not found', e)

    @base.tools.json_response
    def post(self, request: http.HttpRequest, api_version: int, *args, **kwargs):
        try:
            return getattr(self, f'post_v{int(api_version)}')(request, *args, **kwargs)
        except (AttributeError, ValueError) as e:
            return base.web.BaseViewError(status=404).add(f'{api_version=} not found', e)

    # def get_v1(self, request: http.HttpRequest, *args, **kwargs) -> http.HttpResponse:
    #     raise NotImplementedError

    # def post_v1(self, request: http.HttpRequest, *args, **kwargs) -> http.HttpResponse:
    #     raise NotImplementedError


class BaseApiViewController(abc.ABC):
    """Базовый класс контроллера вьюхи

    Под каждую версию эндпоинта предполагается использовать отдельный класс.
    От вьюхи контроллер получает объект HTTP-запроса (данные могут быть в GET, POST, headers и пр).
    Преобразованием в DTO и валидацией занимается контроллер.
    Вьюхе возвращает DTO с ответом.
    """

    _request_dto: type[base.web.BaseViewRequest] = base.web.BaseViewRequest
    _response_dto: type[base.web.BaseViewResponse] = base.web.BaseViewResponse
    _error_dto: type[base.web.BaseViewError] = base.web.BaseViewError

    input_data: _request_dto

    def __init__(self, request: http.HttpRequest):
        self.request = request
        self.input_data = self._get_request_dto()

    @abc.abstractmethod
    def handle_request(self) -> _response_dto:
        """Обрабатывает запрос"""
        raise NotImplementedError

    def parse_input_data(self) -> _request_dto:
        """Парсит входящие данные запроса"""
        return self._parse_input_data_from_get()

    @typing.final
    def _parse_input_data_from_get(self) -> _request_dto:
        """Парсит входящие данные GET-запроса"""
        return self._request_dto.parse_obj(self.request.GET.dict())

    @typing.final
    def _parse_input_data_from_post(self) -> _request_dto:
        """Парсит входящие данные POST-запроса"""
        return self._request_dto.parse_raw(self.request.body)

    @typing.final
    def _get_request_dto(self) -> _request_dto:
        try:
            return self.parse_input_data()
        except pydantic.ValidationError as e:
            error_dto = self._error_dto(status=400, request_structure=self._request_dto.schema())
            raise base.exc.ViewResponse(
                'Некорректные параметры запроса',
                response_dto=error_dto.add(*str(e).splitlines())) from e
