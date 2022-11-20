import logging
import os
import time
import requests
from logging.handlers import RotatingFileHandler
import telegram
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(funcName)s, %(lineno)s, %(levelname)s, %(message)s',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    encoding='UTF-8',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(funcName)s'
)
handler.setFormatter(formatter)

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


def send_message(bot, message):
    """Oтправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение в чат {TELEGRAM_CHAT_ID}: {message}')
    except Exception:
        logger.error('Ошибка отправки сообщения в телеграм')


def get_api_answer(current_timestamp):
    """Запрос к API и возвращение в формате JSON."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
        raise Exception(f'Ошибка при запросе к основному API: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        status_code = homework_statuses.status_code
        logger.error(f'Ошибка {status_code}')
        raise Exception(f'Ошибка {status_code}')
    try:
        return homework_statuses.json()
    except ValueError:
        logger.error('Ошибка парсинга ответа из формата json')
        raise ValueError('Ошибка парсинга ответа из формата json')


def check_response(response):
    """Проверка корректности API-ответа."""
    if type(response) is not dict:
        raise TypeError('Ответ API отличен от словаря')
    try:
        list_works = response['homeworks']
    except KeyError:
        logger.error('Ошибка словаря по ключу homeworks')
        raise KeyError('Ошибка словаря по ключу homeworks')
    try:
        homework = list_works[0]
    except IndexError:
        logger.error('Домашку не делал - список пуст)')
        raise IndexError('Домашку не делал - список пуст)')
    return homework


def parse_status(homework):
    """Получение статуса ДЗ и обновление статуса."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise Exception('Отсутствует ключ "status" в ответе API')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise Exception(f'Неизвестный статус работы: {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        logger.critical('Отсутствуют одна или несколько переменных окружения')
        raise Exception('Отсутствуют одна или несколько переменных окружения')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if not check_response(response):
                logger.debug('Пустой список с необновленным статусом')
                raise Exception('Пустой список с необновленным статусом')
            else:
                send_message(bot, parse_status(
                    check_response(response)
                ))
                logger.info('Успешная отправка сообщения')
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.critical(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
