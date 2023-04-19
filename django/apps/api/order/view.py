from apps import api


class OrderView(api.order.v1.view.OrderView):
    """Общий view для всех версий

    View всех версий подключаются сюда через множественное наследование.
    Этот view указывается в urls.py
    """
    pass
