RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'


class ParseStatusError(Exception):
    """В ответе недокументированный статус."""

    pass


class Not200Error(Exception):
    """Ответ не равен 200."""

    pass


class AnswerApiError(Exception):
    """Ответ API не соответствует ожиданиям."""

    pass


class CheckResponseError(Exception):
    """Response в check_response не соответствует ожиданиям."""

    pass
