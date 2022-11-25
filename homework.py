import logging
import os
import time
import requests
import sys
import telegram
from http import HTTPStatus
from exeptions_castom import ErrorResponseAPI
from exeptions_castom import ErrorStatusCode
from exeptions_castom import ErrorNotTypeDict
from exeptions_castom import ErrorKeyDict
from exeptions_castom import ErrorNotTypeList
from dotenv import load_dotenv

load_dotenv()

# когда пихаю хендлеры в if, то у меня падают тесты и пишет
# что logger is not defined(
# причем интересно, что сам бот запускается без ошибок
# а тесты яндекса сообщают об ошибке)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message: str) -> None:
    """Oтправляет сообщение в Telegram чат."""
    logger.info('Начата отправка сообщений')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение в чат {TELEGRAM_CHAT_ID}: {message}')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения в телеграм {error}')


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос к API и возвращение в формате JSON."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        raise ErrorResponseAPI(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        status_code = response.status_code
        raise ErrorStatusCode(f'Ошибка {status_code}')
    return response.json()


def check_response(response: dict) -> dict:
    """Проверка корректности API-ответа."""
    if not isinstance(response, dict):
        raise ErrorNotTypeDict(
            f'Ответ API отличен от словаря {type(response)}'
        )
    homework = response.get('homeworks')
    if homework is None:
        raise ErrorKeyDict(f'Ошибка по ключу {homework}')
    if not isinstance(response['homeworks'], list):
        raise ErrorNotTypeList(f'Тип данных не список {type(response)}')
    if isinstance(response, list):
        response = response[0]
        logging.info('API передал списко дз')
    return homework


def parse_status(homework: dict) -> str:
    """Получение статуса ДЗ и обновление статуса."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise KeyError('Отсутствует ключ "status" в ответе API')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise Exception(f'Неизвестный статус работы: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_error = ''
    status = ''
    if not check_tokens():
        logger.critical('Отсутствуют одна или несколько переменных окружения')
        sys.exit()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                current_homework = homeworks[0]
                hw_status = parse_status(current_homework)
                message = send_message(bot, f'{hw_status}')
                if message != status:
                    send_message(bot, f'{hw_status}')
                    status = message
            else:
                logger.debug('Нет новых статусов')
            current_timestamp = response.get("current_date")
            last_error = ''
        except Exception as error:
            message = f'Сбой в работе программы {error}'
            if str(error) != str(last_error):
                send_message(bot, message)
                last_error = error
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format=(
            '%(asctime)s, %(funcName)s, %(lineno)d,'
            ' %(levelname)s, %(message)s'
        )
    )
    '''logger = logging.getLogger(__name__)
    logger.addHandler(
    logging.StreamHandler()
    )'''
    main()
