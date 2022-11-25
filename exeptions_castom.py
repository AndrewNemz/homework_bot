class ErrorResponseAPI(Exception):
    """Вызывается, если происхоидт ошибка ответа API."""

    pass


class ErrorStatusCode(Exception):
    """Вызывается, если код страницы недоступен."""

    pass


class ErrorNotTypeDict(TypeError):
    """Вызывается, если ответ API отличен от словаря."""

    pass


class ErrorKeyDict(TypeError):
    """Вызывается, если в словаре есть несуществующий ключ."""

    pass


class ErrorNotTypeList(TypeError):
    """Вызывается, если ответ API отличен от списка."""

    pass
