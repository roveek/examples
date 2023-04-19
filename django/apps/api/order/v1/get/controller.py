from apps import api


class ViewController(api.base.view.BaseApiViewController):

    _request_dto = api.order.v1.get.request.Root
    _response_dto = api.order.v1.get.response.Root

    input_data: _request_dto

    def handle_request(self) -> _response_dto:
        response_dto = self._response_dto()
        response_dto.data.order = {self.input_data.id: 'order'}
        return response_dto
