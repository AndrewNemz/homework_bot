class ErrorResponseAPI(Exception):
    """Вызывается, если происхоидт ошибка ответа API."""

    pass


class ErrorStatusCode(Exception):
    """Вызывается, если код страницы недоступен."""

    pass


class ErrorNotTypeDict(Exception):
    """Вызывается, если ответ API отличен от словаря."""

    pass


class ErrorKeyDict(Exception):
    """Вызывается, если в словаре есть несуществующий ключ."""

    pass


class ErrorNotTypeList(Exception):
    """Вызывается, если ответ API отличен от списка."""

    pass
