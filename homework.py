import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException
from telegram.error import BadRequest, InvalidToken, Unauthorized

load_dotenv()

logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename=os.path.join(os.path.dirname(__file__), 'bot.log'),
    filemode='w',
    level=logging.DEBUG

)

logger = logging.getLogger(__name__)
handler = RotatingFileHandler('bot.log', maxBytes=5000000, backupCount=3)
logger.addHandler(handler)

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['CHAT_ID']
except KeyError:
    logging.exception('Неправильно заданы переменные окружения')
    sys.exit()

PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
STATUS_VERDICT = {
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, работа зачтена!',
    'reviewing': 'Работа взята в ревью.'
}
TIMEOUT = 60 * 23
ERROR_TIMEOUT = 5

try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
except InvalidToken:
    logging.exception('Не удалось инциализировать бота.')
    sys.exit(1)


def parse_homework_status(homework):
    """Функция для получения статуса домашней работы."""

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if (homework_name or homework_status) is None:
        logging.exception('Отсутствуют нужные ключи в homework.')
        raise KeyError('Неверные ключи')

    verdict = STATUS_VERDICT.get(homework_status)
    if verdict is None:
        logging.exception(f'Неизветный ключ для статуса {homework_status}.')
        raise KeyError(f'Неизвестный ключ для статуса. {homework_status}')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    """Функция для получения данных о домашних работах от API
    яндекс практикума."""
    params = {'from_date': int(current_timestamp)}
    response = requests.get(
        url=PRAKTIKUM_URL,
        headers=HEADERS,
        params=params
    )
    homework_statuses = response.json()
    if homework_statuses.get('error') or homework_statuses.get('code'):
        logging.exception(f'При отправке запроса к API возникла ошибка.'
                          f'Параметры запроса url: {PRAKTIKUM_URL}, headers: '
                          f'{HEADERS}, params: {params}')
        error = homework_statuses.get('error')
        code = homework_statuses.get('code')
        raise RequestException(f'{error}, код {code}')

    return homework_statuses


def send_message(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info('Бот послал сообщение!')
    except BadRequest:
        logging.exception('Не получилось отправить сообщение')


def main():
    current_timestamp = int(time.time())
    logging.debug('Бот запущен!')
    while True:
        try:
            response = get_homeworks(current_timestamp)
            all_homework = response.get('homeworks')
            if all_homework:
                new_homework = all_homework[0]
                homework_status = parse_homework_status(new_homework)
                send_message(homework_status)

            time.sleep(TIMEOUT)
            current_timestamp = int(time.time())

        except (KeyError, BadRequest, Unauthorized, RequestException) as e:
            logging.exception(e)
            send_message(f'Бот упал с ошибкой {e}')
            time.sleep(ERROR_TIMEOUT)


if __name__ == '__main__':
    main()
