import typing

import base


class BaseException(Exception):
    """
    BaseException затеняет (только в этом файле) питоний BaseException,
    который бесполезен, поскольку
    "…is not meant to be directly inherited by user-defined classes".
    """
    default_message = 'Непредвиденная ошибка'

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message or self.default_message)


class ViewResponse(BaseException):
    """Используется как вариант ответа API (например с ошибкой)

    Исключение ловится декоратором или в middleware.
    """
    def __init__(self, message: str, response_dto):
        """
        :type response_dto: base.struct.BaseViewResponse
        """
        self.response_dto = response_dto
        super().__init__(message)


class AccessDenied(BaseException):
    pass


class RequestError(BaseException):
    def __init__(self, message: str, status: int = None):
        self.status = status
        super().__init__(message)


class ResponseError(BaseException):
    pass


class DataError(BaseException):
    """Проблема с данными

    pydantic.ValidationError относится сюда же."""
    default_message = 'Ошибка данных'
    data: typing.Any = None

    def __init__(self, message: str = None, data: typing.Any = None):
        if data is not None:
            self.data = data
        super().__init__(message)


class RequestDataError(DataError):
    """Некорректные для запроса данные"""
    pass


class InputDataError(DataError):
    """Некорректные входные данные (тип или значение)"""
    default_message = 'Ошибка входных данных'


class OutputDataError(DataError):
    """Некорректные выходные данные (тип или значение)

    Это может быть ошибка валидации исходящей (от АПИ) структуры данных."""
    default_message = 'Ошибка выходных данных'


class ArgumentError(InputDataError):
    """Некорректный тип или значение аргументов функции или метода"""
    default_message = 'Некорректный тип/значение аргументов функции или метода'


class NotFound(DataError):
    """Не нашли"""
    default_message = 'Не найдено'


class MultipleResults(DataError):
    """Нашли! И много!"""
    default_message = 'Найдено несколько'


class AlreadyExist(DataError):
    """Нашли, но лучше бы не находили…"""
    default_message = 'Уже существует'


class UnsupportedData(DataError):
    """Неподдерживаемый формат/тип/итд данных"""
    default_message = 'Неподдерживаемый тип'


class InternalError(BaseException):
    """Не зависящая от пользователя внутренняя ошибка сервиса"""
