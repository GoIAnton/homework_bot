import time
import sys
import logging
import json
import os

import requests
import telegram
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)

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


class ParseStatusError(Exception):
    """В ответе недокументированный статус."""

    pass


class Not200Error(Exception):
    """Ответ не равен 200."""

    pass


class AnswerApiError(Exception):
    """Ответ API не соответствует ожиданиям."""

    pass


def send_message(bot, message):
    """Отправка сообщения в Телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'В Telegram отправлено cообщение: {message}')
    except telegram.TelegramError as error:
        logger.error(f'В Telegram НЕ отправлено cообщение: {error}')


def get_api_answer(current_timestamp):
    """Получение данных с API Яндекс Практикума за определённый период."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
        if response.status_code != 200:
            msg = (
                f'API Яндекс Практикума недоступена.'
                f' Код ответа {response.status_code}'
            )
            logger.error(msg)
            raise Not200Error(msg)
        return response.json()
    except json.JSONDecodeError as value_error:
        logger.error(f'{value_error}')
        raise json.JSONDecodeError(f'{value_error}')


def check_response(response):
    """Проверяет ответ API и возвращает список домашних работ."""
    homework = response['homeworks']
    if homework == []:
        return {}
    if type(homework[0]) is not dict:
        msg = 'Ответ API не соответствует ожиданиям'
        logger.error(msg)
        raise AnswerApiError(msg)
    return homework


def parse_status(homework):
    """Находит статус и возвращает соответствующее сообщение."""
    if 'homework_name' not in homework or 'status' not in homework:
        logger.error('homework_name или status отсутствует в homework')
        raise KeyError('homework_name или status отсутствует в homework')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        msg = 'В ответе недокументированный статус'
        logger.error(msg)
        raise ParseStatusError(msg)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    msg = 'Отсутствует переменная окружения'
    check = True
    if PRACTICUM_TOKEN is None:
        check = False
        logger.critical(
            f'{msg} PRACTICUM_TOKEN')
    if TELEGRAM_TOKEN is None:
        check = False
        logger.critical(
            f'{msg} TELEGRAM_TOKEN')
    if TELEGRAM_CHAT_ID is None:
        check = False
        logger.critical(
            f'{msg} CHAT_ID')
    return check


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = 'reviewing'
    check_error = " "
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            if status != homework.get('status') and homework:
                message = parse_status(homework)
                send_message(bot, message)
                status = homework.get('status')
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if check_error != message:
                check_error = message
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
