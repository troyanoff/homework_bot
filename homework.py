import logging
import os
import requests
import time
import telegram

from dotenv import load_dotenv

from exceptions import (
    NoKeysException,
    FailSendException,
    DisableEndpointException,
    ProblemEndpointException,
    ProcessingProblemException,
    SurpriseStatusException
)

logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='w'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
hendler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
hendler.setFormatter(formatter)
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

LAST_STATUS = ''


def send_message(bot, message):
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено.')
    except:
        raise FailSendException


def get_api_answer(current_timestamp):
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != 200:
        raise DisableEndpointException
    return homework_statuses.json()


def check_response(response):
    if type(response) != dict and type(response['homeworks']) != dict:
        raise ProblemEndpointException
    if 'homeworks' not in response:
        raise ProcessingProblemException
    if type(response.get('homeworks')) != list:
        raise ProblemEndpointException
    return response.get('homeworks')
    


def parse_status(homework):
    global LAST_STATUS
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    if LAST_STATUS == verdict:
        logger.debug('В ответе отсутствуют новые статусы.')
    else:
        LAST_STATUS = verdict
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    return (TELEGRAM_TOKEN != None
           and TELEGRAM_CHAT_ID != None
           and PRACTICUM_TOKEN != None)


def main():
    """Основная логика работы бота."""

    if check_tokens() == False:
        raise NoKeysException
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    LAST_MESSAGE = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except NoKeysException as error:
            message = NoKeysException.__doc__
            logger.critical(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)
        except FailSendException as error:
            message = FailSendException.__doc__
            logger.error(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)
        except DisableEndpointException as error:
            message = DisableEndpointException.__doc__
            logger.error(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)
        except ProblemEndpointException as error:
            message = ProblemEndpointException.__doc__
            logger.error(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)
        except ProcessingProblemException as error:
            message = ProcessingProblemException.__doc__
            logger.error(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)
        except SurpriseStatusException as error:
            message = SurpriseStatusException.__doc__
            logger.error(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if LAST_MESSAGE != message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                LAST_MESSAGE = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
