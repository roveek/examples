import pydantic

import base


class Data(pydantic.BaseModel):
    order: dict = {}


class Root(base.web.BaseViewResponse):
    """Ответ (api → client)"""
    version: int = 1
    data: Data = pydantic.Field(default_factory=Data)
