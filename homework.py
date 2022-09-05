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
    FailSend,
    DisableEndpoint,
    ProblemEndpoint,
    ProcessingProblem
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
    global LAST_MESSAGE
    try:
        if LAST_MESSAGE != message:
            bot.send_message(TELEGRAM_CHAT_ID, message)
            LAST_MESSAGE = message
            logger.info('Сообщение успешно отправлено.')
    except Exception as error:
        raise FailSend from error


def get_api_answer(current_timestamp):
    """Получения ответа от API."""
    begining_period = current_timestamp or int(time.time())
    params = {'from_date': begining_period}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise DisableEndpoint from error
    if homework_statuses.status_code != HTTPStatus.OK:
        raise DisableEndpoint
    return homework_statuses.json()


def check_response(response):
    """Проверка ответа от API."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем.')
    if 'homeworks' not in response:
        raise ProcessingProblem
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise ProblemEndpoint
    return homeworks


def parse_status(homework):
    """Обработка ответа и вывод статуса работы."""
    global LAST_STATUS, LAST_MESSAGE
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not all((homework_name, homework_status)):
        raise KeyError('В ответе нет нужной информации.')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Неизвестный статус.')
    verdict = HOMEWORK_STATUSES[homework_status]
    fix_status = LAST_STATUS.get(homework_name)
    if homework_name in LAST_STATUS and fix_status == homework_status:
        logger.debug(
            f'В ответе отсутствуют новые статусы для работы {homework_name}.'
        )
        return LAST_MESSAGE
    else:
        LAST_STATUS[homework_name] = verdict
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия переменных окружения."""
    keys = (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN)
    return all(keys)


def except_return(bot, error):
    """Обработка исключений."""
    if not isinstance(error, KittyBotExceptions):
        message = f'Сбой в работе программы: {error}'
    else:
        message = error.__doc__
    if isinstance(error, NoKeys):
        logger.critical(message)
    else:
        logger.error(message)
    send_message(bot, message)
    time.sleep(RETRY_TIME)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Бот остановлен из-за отсутствия ключей.')
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            except_return(bot, error)


if __name__ == '__main__':
    main()
