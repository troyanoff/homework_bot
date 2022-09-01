import logging
import os
import requests
import time
import telegram


from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import (
    KittyBotExceptions,
    NoKeys,
    DisableEndpoint,
    ProblemEndpoint,
    ProcessingProblem,
    SurpriseStatus
)


logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='w'
)

logger = logging.getLogger(__name__)
hendler = logging.StreamHandler()
logger.addHandler(hendler)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

LAST_STATUS = {}
LAST_MESSAGE = ''


def send_message(bot, message):
    """Отправка сообщения ботом."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info('Сообщение успешно отправлено.')


def get_api_answer(current_timestamp):
    """Получения ответа от API."""
    if current_timestamp is None:
        raise ProblemEndpoint
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'При обращении к сервису возникла ошибка - {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        raise DisableEndpoint
    return homework_statuses.json()


def check_response(response):
    """Проверка ответа от API."""
    if not isinstance(response, dict):
        raise ProblemEndpoint
    if 'homeworks' not in response:
        raise ProcessingProblem
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise ProblemEndpoint
    return homeworks


def parse_status(homework):
    """Обработка ответа и вывод статуса работы."""
    global LAST_STATUS
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if any((homework_name, homework_status)) is None:
        raise ProcessingProblem
    if homework_status not in HOMEWORK_STATUSES:
        raise SurpriseStatus
    verdict = HOMEWORK_STATUSES[homework_status]
    fix_status = LAST_STATUS.get(homework_name)
    if homework_name in LAST_STATUS and fix_status == homework_status:
        logger.debug('В ответе отсутствуют новые статусы.')
    else:
        fix_status = verdict
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия переменных окружения."""
    keys = (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN)
    return all(keys)


def except_return(bot, exception_name):
    """Обработка исключений."""
    global LAST_MESSAGE
    if not isinstance(exception_name, KittyBotExceptions):
        message = f'Сбой в работе программы: {exception_name}'
    message = exception_name.__doc__
    if isinstance(exception_name, NoKeys):
        logger.critical(message)
    else:
        logger.error(message)
    if LAST_MESSAGE != message:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        LAST_MESSAGE = message
    time.sleep(RETRY_TIME)


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0

    while True:
        try:
            if not check_tokens():
                raise NoKeys
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            # "В качестве параметра функция получает
            # только один элемент из списка домашних работ."
            # Цитата из ТЗ. Проверка ответа произведена в check_response().
            message = parse_status(homeworks[0])
            send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception:
            except_return(bot, Exception)


if __name__ == '__main__':
    main()
