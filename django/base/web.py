import enum

import pydantic


class ViewResponseStatus(str, enum.Enum):
    OK = 'OK'
    SUCCESS = 'Success'
    PARTIAL_SUCCESS = 'Partial success'
    FINISHED = 'Finished'
    COMPLETE = 'Complete'
    FAIL = 'Fail'
    NOT_FOUND = 'Not found'


class BaseViewDto(pydantic.BaseModel):
    """Базовый класс для API"""

    class Config:
        validate_all = True
        extra = pydantic.Extra.ignore


class BaseViewRequest(BaseViewDto):
    """Базовый класс API запроса"""
    pass


class BaseViewResponse(BaseViewDto):
    """Базовый класс API ответа"""
    version: int = 1
    status: ViewResponseStatus = ViewResponseStatus.OK
    data: dict = None


class BaseViewError(BaseViewResponse):
    """Базовый класс ошибки API"""
    status: int = 500
    errors: list[str] = []
    request_structure: dict = None

    def __str__(self):
        return '[%s] ошибок: %s' % (self.status, len(self.errors))

    def add(self, *errors: str | Exception):
        for error in errors:
            self.errors.append(str(error))
        return self
