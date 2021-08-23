import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}

bot = telegram.Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='bot.log',
    filemode='w',
    level=logging.DEBUG

)

logger = logging.getLogger(__name__)
handler = RotatingFileHandler('bot.log', maxBytes=5000000, backupCount=3)
logger.addHandler(handler)


def parse_homework_status(homework):
    """Функция для получения статуса домашней работы."""
    homework_name = homework.get('homework_name')
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    """Функция для получения данных о домашних работах от API
    яндекс практикума."""
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        url=PRAKTIKUM_URL,
        headers=HEADERS,
        params=params
    )
    return homework_statuses.json()


def send_message(message):
    logging.info('Бот послал сообщение!')
    return bot.send_message(chat_id=CHAT_ID, text=message)


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

            time.sleep(23 * 60)
            current_timestamp = int(time.time())

        except Exception as e:
            logging.exception(e)
            send_message(f'Бот упал с ошибкой {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
