class KittyBotExceptions(Exception):
    """Kittybot нашел ошибку."""


class NoKeys(KittyBotExceptions):
    """Отсутствует элемент переменного окружения."""

    pass


class FailSend(KittyBotExceptions):
    """Сбой отправки сообщения в телеграмм."""

    pass


class DisableEndpoint(KittyBotExceptions):
    """Указанный эндпоинт недоступен."""

    pass


class ProblemEndpoint(KittyBotExceptions):
    """Сбой в обращении к эндпоинту."""

    pass


class ProcessingProblem(KittyBotExceptions):
    """Отсутствие ожидаемых ключей в ответе API."""

    pass


class NoHomeworksInList(KittyBotExceptions):
    """В указаном периоде нет проверяемых работ."""

    pass
