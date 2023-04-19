import pydantic

import base


class Root(base.web.BasseViewRequest):
    """Запрос (client → api) на поиск"""
    id: int = pydantic.Field(title='id заказа')
