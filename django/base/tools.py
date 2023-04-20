import collections.abc
import copy
import datetime
import functools
import logging
import time
import typing

import django.db
import django.http
import psycopg2
import pydantic

import base

log = logging.getLogger(__name__)


class UrlPath(str):
    """Для манипуляций с путем URL'a"""

    def __add__(self, other) -> 'UrlPath':
        return self.__class__(super().__add__(other))

    def __repr__(self) -> str:
        return "%s('%s')" % (self.__class__.__name__, self)

    def __truediv__(self, other) -> 'UrlPath':  # /
        path = '%s/%s' % (self.rstrip('/'), str(other).lstrip('/'))
        return self.__class__(path)

    def slash(self, text: str) -> 'UrlPath':
        return self / text

    @property
    def strip_rslash(self) -> 'UrlPath':
        """Удаляет слэш справа"""
        return self.__class__(self.rstrip('/'))

    @property
    def strip_lslash(self) -> 'UrlPath':
        """Удаляет слэш слева"""
        return self.__class__(self.lstrip('/'))

    @property
    def with_rslash(self) -> 'UrlPath':
        """Добавляет слэш справа"""
        return self.__class__(self.strip_rslash + '/')

    @property
    def with_lslash(self) -> 'UrlPath':
        """Добавляет слэш слева"""
        return self.__class__('/' + self.strip_lslash)

    @property
    def only_rslash(self) -> 'UrlPath':
        """Удаляет слэш слева и добавляет справа"""
        return self.strip_lslash.with_rslash


class Raise:
    """Райзит исключение, если условие вызванного метода выполняется

    Этот механизм нужен для рерайза исключений по условию и,
    как раз, и скрывает в своих недрах некрасивые if'ы.
    """

    def __init__(self, exc_to_raise: Exception):
        self.exc_to_raise = exc_to_raise

    @classmethod
    def if_db_error(cls, exc: Exception, data: typing.Any | None = None):
        """Рерайзит известные БД-исключения

        :raises base.exc.AlreadyExistError:
        :raises base.exc.InputDataError:
        """
        if not isinstance(exc, django.db.IntegrityError):
            return

        error = ' | '.join([line.strip() for line in str(exc).splitlines()])

        cls(base.exc.AlreadyExistError(f'Уже существует ({error})', data)
            ).if_db_unique_violation(exc)

        cls(base.exc.InputDataError(f'None вместо значения ({error})', data)
            ).if_db_not_null_violation(exc)

    def if_db_unique_violation(self, exc: django.db.IntegrityError):
        """Райзит, если БД-исключение – UniqueViolation"""
        if isinstance(exc.__context__, psycopg2.errors.UniqueViolation):
            self._raise(cause=exc)

    def if_db_not_null_violation(self, exc: django.db.IntegrityError):
        """Райзит, если БД-исключение – NotNullViolation"""
        if isinstance(exc.__context__, psycopg2.errors.NotNullViolation):
            self._raise(cause=exc)

    def if_no_data(self, exc: pydantic.ValidationError):
        """Райзит, если все ошибки валидации — type_error.none.not_allowed

        Задумано для ситуаций, когда для формирования какого-то ДТО
        недостаточно данных, но их можно откуда-то запросить, дополнить
        и повторить вызов метода с уже достаточными данными.

        Исключение base.exc.InsufficientData для этой же ситуации.
        """
        if all(map(lambda e: e['type'] == 'type_error.none.not_allowed', exc.errors())):
            self._raise(cause=exc)

    def _raise(self, cause: Exception):
        raise self.exc_to_raise from cause


def iter_exc(e: Exception) -> collections.abc.Iterable[str]:
    """Генератор, возвращающий цепочку исключений."""
    yield str(e) or e.__class__.__name__
    if getattr(e, '__context__', None):
        yield from iter_exc(e.__context__)


def json_response(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except base.exc.ViewResponse as e:
            result = e.response_dto
        except Exception as e:
            log.exception('Неперхваченная ошибка во view %s()', func.__name__)
            result = base.web.BaseViewError().add(
                'Произошла неперехваченная ошибка', *iter_exc(e))
        if isinstance(result, base.web.BaseViewResponse):
            by_alias = getattr(result.Config, 'by_alias', True)
            return django.http.JsonResponse(result.dict(by_alias=by_alias))
        return result

    return wrapped


def retry_if_exception(
        exceptions: typing.Type[Exception] | collections.abc.Iterable[typing.Type[Exception]],
        *, retries: int | list[float | int] = 2,
        delay_sec: float = 0, geom_progression: float = 1,
        extra_check: typing.Callable[[Exception], bool] = None):
    """Декоратор, вызывающий метод/функцию повторно

    Работает только в случае, если поймает указанное исключение (-я).

    :param exceptions:
        исключение/список исключений при которых возникает повтор
    :param retries: [число] – количество повторов,
        [массив чисел] – это таймауты
        (delay_sec и geom_progression при этом игнорируются)
    :param delay_sec: задержка между повторами (в секундах)
    :param geom_progression:
        умножает delay_sec на указанное значение с каждым следующим повтором
    :param extra_check: функция, куда будет передано перехваченное
        исключение. Если функция вернет False – повторных вызовов не будет.
        Используется если исключение имеет что-то, например code/status,
        и нужны повторы только при определённом коде.
    """
    def decorator(func):

        @functools.wraps(func)
        def decorated_func(*args, **kwargs):
            nonlocal delay_sec, retries
            delays = copy.deepcopy(retries) if isinstance(retries, list) else \
                [delay_sec * geom_progression**i for i in range(retries)]
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if not delays:
                        raise  # все ретраи отработаны
                    if callable(extra_check) and bool(extra_check(e)) is False:
                        raise  # extra_check не пройден – повтора не будет
                    time.sleep(delays.pop(0))

        return decorated_func

    return decorator


class Runtime:
    """Класс для измерения времени выполнения кода.

    Вариант использования 1:
    >>> timer = Runtime().start()
    >>> # Или timer = Runtime(start=True)
    >>> print('some work')
    >>> timer.stop()
    >>> print(timer)

    Вариант использования 2:
    >>> with Runtime() as timer:
    >>>     print('some work')
    >>> print(timer)

    Вариант использования 3:
    >>> def save_measure(seconds: float):
    >>>     print(seconds)
    >>>
    >>> @Runtime.decorator(on_finish=save_measure)
    >>> def func():
    >>>     print('some work')
    """
    def __init__(self, *, start: bool = False):
        self._start = None
        self._runtime = None
        if start:
            self.start()

    def __str__(self) -> str:
        """Человекопонятное описание для дебаггера и логов."""
        if self._start:
            return 'timer (running): %s' % self.as_clock
        elif self._runtime:
            return 'timer (stopped): %s' % self.as_clock
        return 'timer was not started'

    def __repr__(self):
        return self.__str__()

    def __float__(self) -> float:
        return self.elapsed or 0.0

    def __enter__(self) -> 'Runtime':
        """Context manager.

        >>> with Runtime() as timer:
        >>>    print('do something')
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self) -> 'Runtime':
        self._runtime = None
        self._start = time.perf_counter()
        return self

    @property
    def elapsed(self) -> float | None:
        if self._start:
            return time.perf_counter() - self._start
        return self._runtime

    def stop(self) -> float | None:
        if self._start:
            self._runtime = self.elapsed
            self._start = None
        return self._runtime

    @property
    def as_clock(self) -> str | None:
        if self._start:
            return str(datetime.timedelta(seconds=self.elapsed))
        elif self._runtime:
            return str(datetime.timedelta(seconds=self._runtime))

    @property
    def as_text(self):
        return self.as_clock

    @staticmethod
    def decorator(*, on_finish: typing.Callable = None):
        def wrapper(func):
            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                with Runtime() as _timer:
                    result = func(*args, **kwargs)
                if on_finish is None:
                    log.debug('function "%s": %s', func.__name__, _timer)
                else:
                    on_finish(_timer)
                return result
            return wrapped
        return wrapper


class ObjectsListLookup:

    def __init__(self, items: list, obj_key_attr: str, obj_value_attr: str):
        """
        :param items: массив объектов
        :param obj_key_attr: атрибут-ключ объекта
        :param obj_value_attr: атрибут-зачение объекта
        """
        self.items = items or []
        self.obj_key_attr = obj_key_attr
        self.obj_value_attr = obj_value_attr

    def __getitem__(self, key_name) -> str | None:
        for item in self.items:
            if getattr(item, self.obj_key_attr) == key_name:
                return getattr(item, self.obj_value_attr)
