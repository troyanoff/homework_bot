class NoKeysException(Exception):
    """Отсутствует элемент переменного окружения."""

    pass


class FailSendException(Exception):
    """Сбой отправки сообщения в телеграмм."""

    pass


class DisableEndpointException(Exception):
    """Указанный эндпоинт недоступен."""

    pass


class ProblemEndpointException(Exception):
    """Сбой в обращении к эндпоинту."""

    pass


class ProcessingProblemException(Exception):
    """Отсутствие ожидаемых ключей в ответе API."""

    pass


class SurpriseStatusException(Exception):
    """Обнаружен недокументированный статус работы."""

    pass
